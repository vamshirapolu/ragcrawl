"""Crawl frontier for URL queue management."""

import asyncio
import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from ragcrawl.filters.link_filter import LinkFilter
from ragcrawl.filters.url_normalizer import URLNormalizer
from ragcrawl.models.frontier_item import FrontierItem, FrontierStatus
from ragcrawl.utils.hashing import compute_doc_id


@dataclass(order=True)
class PrioritizedItem:
    """Item in the priority queue."""

    priority: float
    item: FrontierItem = field(compare=False)


class Frontier:
    """
    Crawl frontier managing the URL queue.

    Features:
    - Priority-based ordering
    - Deduplication
    - Depth tracking
    - Per-domain bucketing
    """

    def __init__(
        self,
        run_id: str,
        site_id: str,
        link_filter: LinkFilter,
        max_depth: int = 10,
        max_pages: int = 1000,
    ) -> None:
        """
        Initialize the frontier.

        Args:
            run_id: Current crawl run ID.
            site_id: Site being crawled.
            link_filter: Filter for URL validation.
            max_depth: Maximum crawl depth.
            max_pages: Maximum pages to crawl.
        """
        self.run_id = run_id
        self.site_id = site_id
        self.link_filter = link_filter
        self.max_depth = max_depth
        self.max_pages = max_pages

        self.normalizer = URLNormalizer()

        # Priority queue
        self._queue: list[PrioritizedItem] = []

        # Tracking sets
        self._seen_urls: set[str] = set()
        self._in_progress: set[str] = set()
        self._completed: set[str] = set()
        self._failed: set[str] = set()

        # Per-domain tracking
        self._domain_counts: dict[str, int] = {}

        # Stats
        self._discovered_count = 0
        self._max_depth_seen = 0

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def add(
        self,
        url: str,
        depth: int = 0,
        referrer_url: str | None = None,
        priority: float | None = None,
    ) -> bool:
        """
        Add a URL to the frontier.

        Args:
            url: URL to add.
            depth: Depth from seed.
            referrer_url: URL that linked to this.
            priority: Custom priority (higher = sooner).

        Returns:
            True if URL was added, False if filtered/duplicate.
        """
        async with self._lock:
            # Check limits
            if self._discovered_count >= self.max_pages:
                return False

            if depth > self.max_depth:
                return False

            # Filter and normalize
            result = self.link_filter.filter(
                url,
                check_seen=False,
                current_depth=depth,
                max_depth=self.max_depth,
            )

            if not result.allowed:
                return False

            normalized_url = result.normalized_url or self.normalizer.normalize(url)

            # Deduplication
            if normalized_url in self._seen_urls:
                return False

            self._seen_urls.add(normalized_url)
            self._discovered_count += 1
            self._max_depth_seen = max(self._max_depth_seen, depth)

            # Calculate priority
            if priority is None:
                priority = self._calculate_priority(depth, normalized_url)

            # Create frontier item
            domain = self._get_domain(normalized_url)
            url_hash = compute_doc_id(normalized_url)

            item = FrontierItem(
                item_id=f"{self.run_id}_{url_hash}",
                run_id=self.run_id,
                site_id=self.site_id,
                url=url,
                normalized_url=normalized_url,
                url_hash=url_hash,
                depth=depth,
                referrer_url=referrer_url,
                priority=priority,
                status=FrontierStatus.PENDING,
                discovered_at=datetime.now(),
                domain=domain,
            )

            # Add to priority queue (negative priority for max-heap behavior)
            heapq.heappush(self._queue, PrioritizedItem(-priority, item))

            # Track domain
            self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1

            return True

    async def add_seeds(self, seeds: list[str]) -> int:
        """
        Add seed URLs to the frontier.

        Args:
            seeds: List of seed URLs.

        Returns:
            Number of seeds added.
        """
        added = 0
        for seed in seeds:
            if await self.add(seed, depth=0, priority=1000.0):  # High priority for seeds
                added += 1
        return added

    async def add_batch(
        self,
        urls: list[str],
        depth: int,
        referrer_url: str | None = None,
    ) -> int:
        """
        Add multiple URLs to the frontier.

        Args:
            urls: URLs to add.
            depth: Depth for all URLs.
            referrer_url: Referrer URL.

        Returns:
            Number of URLs added.
        """
        added = 0
        for url in urls:
            if await self.add(url, depth, referrer_url):
                added += 1
        return added

    async def get_next(self) -> FrontierItem | None:
        """
        Get the next URL to crawl.

        Returns:
            Next FrontierItem or None if empty.
        """
        async with self._lock:
            while self._queue:
                prioritized = heapq.heappop(self._queue)
                item = prioritized.item

                # Skip if already processed
                if item.normalized_url in self._completed:
                    continue
                if item.normalized_url in self._failed:
                    continue
                if item.normalized_url in self._in_progress:
                    continue

                # Mark in progress
                self._in_progress.add(item.normalized_url)
                item.mark_in_progress()

                return item

            return None

    async def get_batch(self, count: int = 10) -> list[FrontierItem]:
        """
        Get multiple URLs to crawl.

        Args:
            count: Number of URLs to get.

        Returns:
            List of FrontierItems.
        """
        items = []
        for _ in range(count):
            item = await self.get_next()
            if item is None:
                break
            items.append(item)
        return items

    async def mark_completed(self, url: str) -> None:
        """Mark a URL as completed."""
        async with self._lock:
            normalized = self.normalizer.normalize(url)
            self._in_progress.discard(normalized)
            self._completed.add(normalized)

    async def mark_failed(self, url: str, error: str | None = None) -> None:
        """Mark a URL as failed."""
        async with self._lock:
            normalized = self.normalizer.normalize(url)
            self._in_progress.discard(normalized)
            self._failed.add(normalized)

    async def return_to_queue(self, item: FrontierItem) -> None:
        """Return an item to the queue for retry."""
        async with self._lock:
            self._in_progress.discard(item.normalized_url)
            item.status = FrontierStatus.PENDING
            item.retry_count += 1

            # Lower priority on retry
            new_priority = item.priority * 0.5
            heapq.heappush(self._queue, PrioritizedItem(-new_priority, item))

    def _calculate_priority(self, depth: int, url: str) -> float:
        """
        Calculate priority for a URL.

        Higher priority = crawled sooner.
        """
        # Base priority inversely related to depth
        priority = 100.0 / (depth + 1)

        # Boost for documentation-like paths
        doc_indicators = ["/docs", "/guide", "/tutorial", "/api", "/reference"]
        for indicator in doc_indicators:
            if indicator in url.lower():
                priority *= 1.5
                break

        # Lower priority for archive/old paths
        old_indicators = ["/archive", "/old", "/legacy", "/deprecated"]
        for indicator in old_indicators:
            if indicator in url.lower():
                priority *= 0.5
                break

        return priority

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""

    @property
    def size(self) -> int:
        """Current queue size."""
        return len(self._queue)

    @property
    def discovered_count(self) -> int:
        """Total URLs discovered."""
        return self._discovered_count

    @property
    def completed_count(self) -> int:
        """Total URLs completed."""
        return len(self._completed)

    @property
    def failed_count(self) -> int:
        """Total URLs failed."""
        return len(self._failed)

    @property
    def in_progress_count(self) -> int:
        """URLs currently in progress."""
        return len(self._in_progress)

    @property
    def max_depth_reached(self) -> int:
        """Maximum depth seen."""
        return self._max_depth_seen

    @property
    def is_empty(self) -> bool:
        """Check if frontier is empty."""
        return len(self._queue) == 0 and len(self._in_progress) == 0

    def get_stats(self) -> dict[str, Any]:
        """Get frontier statistics."""
        return {
            "queue_size": self.size,
            "discovered": self._discovered_count,
            "completed": len(self._completed),
            "failed": len(self._failed),
            "in_progress": len(self._in_progress),
            "max_depth_reached": self._max_depth_seen,
            "domains": len(self._domain_counts),
        }

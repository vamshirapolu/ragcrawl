"""Incremental sync job for detecting and processing changes."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ragcrawl.config.sync_config import SyncConfig, SyncStrategy
from ragcrawl.extraction.extractor import ContentExtractor
from ragcrawl.fetcher.base import FetchStatus
from ragcrawl.fetcher.crawl4ai_fetcher import Crawl4AIFetcher
from ragcrawl.fetcher.revalidation import RevalidationStatus, Revalidator
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.storage.backend import StorageBackend, create_storage_backend
from ragcrawl.sync.change_detector import ChangeDetector
from ragcrawl.sync.sitemap_parser import SitemapParser
from ragcrawl.utils.hashing import generate_run_id, generate_version_id
from ragcrawl.utils.logging import CrawlLoggerAdapter, get_logger
from ragcrawl.utils.metrics import MetricsCollector

logger = get_logger(__name__)


@dataclass
class SyncResult:
    """Result of a sync job."""

    run_id: str
    site_id: str
    success: bool
    stats: CrawlStats = field(default_factory=CrawlStats)
    changed_pages: list[str] = field(default_factory=list)
    deleted_pages: list[str] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0


class SyncJob:
    """
    Incremental sync job for detecting content changes.

    Uses multiple strategies:
    1. Sitemap lastmod (if available)
    2. HTTP conditional requests (ETag/Last-Modified)
    3. Content hash diffing (fallback)
    """

    def __init__(self, config: SyncConfig) -> None:
        """
        Initialize sync job.

        Args:
            config: Sync configuration.
        """
        self.config = config
        self.site_id = config.site_id
        self.run_id = generate_run_id()

        # Components
        self._storage: StorageBackend | None = None
        self._fetcher: Crawl4AIFetcher | None = None
        self._extractor: ContentExtractor | None = None
        self._sitemap_parser: SitemapParser | None = None
        self._change_detector: ChangeDetector | None = None
        self._revalidator: Revalidator | None = None

        # Tracking
        self._metrics = MetricsCollector()
        self._logger = CrawlLoggerAdapter(self.run_id, self.site_id)
        self._changed_pages: list[str] = []
        self._deleted_pages: list[str] = []

    def _init_components(self) -> None:
        """Initialize components."""
        self._storage = create_storage_backend(self.config.storage)
        self._storage.initialize()

        self._fetcher = Crawl4AIFetcher()
        self._extractor = ContentExtractor()
        self._sitemap_parser = SitemapParser()
        self._change_detector = ChangeDetector(
            normalize=self.config.normalize_for_hash,
            noise_patterns=self.config.hash_noise_patterns,
        )
        self._revalidator = Revalidator(
            use_etag=self.config.use_etag,
            use_last_modified=self.config.use_last_modified,
        )

    async def run(self) -> SyncResult:
        """
        Execute the sync job.

        Returns:
            SyncResult with changed and deleted pages.
        """
        start_time = datetime.now()

        try:
            self._init_components()

            # Verify site exists
            site = self._storage.get_site(self.site_id)
            if not site:
                raise ValueError(f"Site not found: {self.site_id}")

            # Create sync run record
            crawl_run = CrawlRun(
                run_id=self.run_id,
                site_id=self.site_id,
                is_sync=True,
                config_snapshot=self.config.model_dump(
                    exclude={"on_page", "on_change_detected", "on_deletion_detected", "on_error"}
                ),
            )
            crawl_run.mark_started()
            self._storage.save_run(crawl_run)

            # Get pages to check
            pages = await self._get_pages_to_check()

            logger.info("Starting sync", site_id=self.site_id, pages_to_check=len(pages))

            # Process pages
            for page in pages:
                await self._process_page(page)

                # Check limit
                if self.config.max_pages and self._metrics.metrics.pages_crawled >= self.config.max_pages:
                    break

            # Finalize
            metrics = self._metrics.finalize()
            crawl_run.stats = CrawlStats(
                pages_crawled=metrics.pages_crawled,
                pages_changed=metrics.pages_changed,
                pages_unchanged=metrics.pages_unchanged,
                pages_deleted=metrics.pages_deleted,
                pages_failed=metrics.pages_failed,
            )
            crawl_run.mark_completed(partial=metrics.pages_failed > 0)
            self._storage.save_run(crawl_run)

            # Update site
            site.last_sync_at = datetime.now()
            self._storage.save_site(site)

            duration = (datetime.now() - start_time).total_seconds()

            return SyncResult(
                run_id=self.run_id,
                site_id=self.site_id,
                success=True,
                stats=crawl_run.stats,
                changed_pages=self._changed_pages,
                deleted_pages=self._deleted_pages,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error("Sync job failed", error=str(e))
            return SyncResult(
                run_id=self.run_id,
                site_id=self.site_id,
                success=False,
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        finally:
            if self._fetcher:
                await self._fetcher.close()
            if self._storage:
                self._storage.close()

    async def _get_pages_to_check(self) -> list[Page]:
        """Get list of pages to check for changes."""
        # Get pages needing recrawl
        pages = self._storage.get_pages_needing_recrawl(
            self.site_id,
            max_age_hours=self.config.max_age_hours,
            limit=self.config.max_pages or 10000,
        )

        # Apply patterns
        if self.config.include_patterns or self.config.exclude_patterns:
            from ragcrawl.filters.patterns import PatternMatcher

            matcher = PatternMatcher(
                include_patterns=self.config.include_patterns,
                exclude_patterns=self.config.exclude_patterns,
            )
            pages = [p for p in pages if matcher.should_include(p.url)]

        # Try sitemap prioritization
        if SyncStrategy.SITEMAP in self.config.strategy:
            pages = await self._prioritize_by_sitemap(pages)

        return pages

    async def _prioritize_by_sitemap(self, pages: list[Page]) -> list[Page]:
        """Prioritize pages using sitemap lastmod."""
        if not self.config.sitemap_urls:
            # Try to discover sitemap
            site = self._storage.get_site(self.site_id)
            if site and site.seeds:
                from urllib.parse import urljoin

                sitemap_url = urljoin(site.seeds[0], "/sitemap.xml")
                self.config.sitemap_urls = [sitemap_url]

        if not self.config.sitemap_urls:
            return pages

        try:
            # Parse sitemap
            sitemap_entries = await self._sitemap_parser.parse(self.config.sitemap_urls[0])

            # Build lookup
            sitemap_lastmod: dict[str, datetime | None] = {}
            for entry in sitemap_entries:
                sitemap_lastmod[entry.loc] = entry.lastmod

            # Filter and prioritize
            if self.config.respect_sitemap_lastmod:
                filtered_pages = []
                for page in pages:
                    lastmod = sitemap_lastmod.get(page.url)
                    if lastmod and page.last_crawled and lastmod <= page.last_crawled:
                        # Skip if sitemap says unchanged
                        self._metrics.record_unchanged()
                        continue
                    filtered_pages.append(page)
                return filtered_pages

            return pages

        except Exception as e:
            logger.warning("Sitemap parsing failed", error=str(e))
            return pages

    async def _process_page(self, page: Page) -> None:
        """Process a single page for changes."""
        try:
            # Try conditional request first
            if SyncStrategy.HEADERS in self.config.strategy:
                if self._revalidator.has_validators(page.etag, page.last_modified):
                    result = await self._check_with_headers(page)
                    if result is not None:
                        return

            # Full fetch and hash compare
            await self._full_check(page)

        except Exception as e:
            logger.error("Error processing page", url=page.url, error=str(e))
            self._metrics.record_error(type(e).__name__)

            if self.config.on_error:
                try:
                    self.config.on_error(page.url, e)
                except Exception:
                    pass

    async def _check_with_headers(self, page: Page) -> bool | None:
        """
        Check for changes using conditional headers.

        Returns:
            True if not modified, False if modified, None if couldn't determine.
        """
        headers = self._revalidator.get_conditional_headers(
            page.etag, page.last_modified
        )

        fetch_result = await self._fetcher.fetch(
            page.url,
            etag=page.etag,
            last_modified=page.last_modified,
        )

        self._metrics.record_fetch(
            domain=self._get_domain(page.url),
            status_code=fetch_result.status_code or 0,
            latency_ms=fetch_result.latency_ms,
            bytes_downloaded=fetch_result.content_length or 0,
            success=fetch_result.is_success or fetch_result.is_not_modified,
        )

        if fetch_result.is_not_modified:
            # Content unchanged
            self._metrics.record_unchanged()
            page.last_crawled = datetime.now()
            self._storage.save_page(page)
            return True

        if fetch_result.is_not_found:
            # Page deleted
            await self._mark_deleted(page, fetch_result.status_code or 404)
            return True

        if fetch_result.is_success:
            # Content modified, do full extraction
            await self._process_changed_page(page, fetch_result)
            return False

        return None

    async def _full_check(self, page: Page) -> None:
        """Full fetch and hash compare."""
        fetch_result = await self._fetcher.fetch(page.url)

        self._metrics.record_fetch(
            domain=self._get_domain(page.url),
            status_code=fetch_result.status_code or 0,
            latency_ms=fetch_result.latency_ms,
            bytes_downloaded=fetch_result.content_length or 0,
            success=fetch_result.is_success,
        )

        if fetch_result.is_not_found:
            await self._mark_deleted(page, fetch_result.status_code or 404)
            return

        if not fetch_result.is_success:
            page.error_count += 1
            page.last_error = fetch_result.error
            self._storage.save_page(page)
            self._metrics.record_error("fetch_failed")
            return

        # Extract and compare
        extraction = self._extractor.extract(fetch_result, page.url)

        if self._change_detector.has_changed(page.content_hash, extraction.content_hash):
            await self._process_changed_page(page, fetch_result, extraction)
        else:
            self._metrics.record_unchanged()
            page.last_crawled = datetime.now()
            page.etag = fetch_result.etag
            page.last_modified = fetch_result.last_modified
            self._storage.save_page(page)

    async def _process_changed_page(
        self, page: Page, fetch_result: Any, extraction: Any = None
    ) -> None:
        """Process a page that has changed."""
        now = datetime.now()

        if extraction is None:
            extraction = self._extractor.extract(fetch_result, page.url)

        # Create new version
        version_id = generate_version_id(extraction.content_hash)

        version = PageVersion(
            version_id=version_id,
            page_id=page.page_id,
            site_id=self.site_id,
            run_id=self.run_id,
            markdown=extraction.markdown,
            html=extraction.html,
            content_hash=extraction.content_hash,
            url=page.url,
            title=extraction.metadata.title,
            description=extraction.metadata.description,
            status_code=fetch_result.status_code or 200,
            outlinks=extraction.outlinks,
            etag=fetch_result.etag,
            last_modified=fetch_result.last_modified,
            crawled_at=now,
        )

        self._storage.save_version(version)

        # Update page
        old_hash = page.content_hash
        page.current_version_id = version_id
        page.content_hash = extraction.content_hash
        page.etag = fetch_result.etag
        page.last_modified = fetch_result.last_modified
        page.last_crawled = now
        page.last_changed = now
        page.version_count += 1
        page.error_count = 0

        self._storage.save_page(page)

        self._metrics.record_change()
        self._changed_pages.append(page.url)
        self._logger.content_changed(page.url, old_hash, extraction.content_hash)

        # Callback
        if self.config.on_change_detected:
            try:
                self.config.on_change_detected(page, version)
            except Exception as e:
                logger.warning("on_change_detected error", error=str(e))

    async def _mark_deleted(self, page: Page, status_code: int) -> None:
        """Mark a page as deleted."""
        if not self.config.detect_deletions:
            return

        page.error_count += 1

        if page.error_count >= self.config.deletion_threshold:
            # Create tombstone
            now = datetime.now()
            version_id = generate_version_id("tombstone", now)

            version = PageVersion(
                version_id=version_id,
                page_id=page.page_id,
                site_id=self.site_id,
                run_id=self.run_id,
                markdown="",
                content_hash="tombstone",
                url=page.url,
                status_code=status_code,
                crawled_at=now,
                is_tombstone=True,
            )

            self._storage.save_version(version)

            page.is_tombstone = True
            page.status_code = status_code
            page.last_crawled = now
            page.current_version_id = version_id

            self._storage.save_page(page)

            self._metrics.record_deletion()
            self._deleted_pages.append(page.url)
            self._logger.tombstone_created(page.url, status_code)

            # Callback
            if self.config.on_deletion_detected:
                try:
                    self.config.on_deletion_detected(page)
                except Exception as e:
                    logger.warning("on_deletion_detected error", error=str(e))
        else:
            page.last_crawled = datetime.now()
            self._storage.save_page(page)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse

        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

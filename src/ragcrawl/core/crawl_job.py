"""Main crawl job orchestration."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.core.frontier import Frontier
from ragcrawl.core.scheduler import DomainScheduler
from ragcrawl.extraction.extractor import ContentExtractor
from ragcrawl.fetcher.base import FetchStatus
from ragcrawl.fetcher.crawl4ai_fetcher import Crawl4AIFetcher
from ragcrawl.fetcher.robots import RobotsChecker
from ragcrawl.filters.link_filter import LinkFilter
from ragcrawl.filters.quality_gates import QualityGate
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats
from ragcrawl.models.document import Document, DocumentDiagnostics, HeadingInfo
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site
from ragcrawl.storage.backend import StorageBackend, create_storage_backend
from ragcrawl.utils.hashing import (
    compute_content_hash,
    compute_doc_id,
    generate_run_id,
    generate_site_id,
    generate_version_id,
)
from ragcrawl.utils.logging import CrawlLoggerAdapter, get_logger
from ragcrawl.utils.metrics import MetricsCollector

logger = get_logger(__name__)


@dataclass
class CrawlResult:
    """Result of a crawl job."""

    run_id: str
    site_id: str
    success: bool
    stats: CrawlStats = field(default_factory=CrawlStats)
    documents: list[Document] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0


class CrawlJob:
    """
    Main crawl job orchestrator.

    Coordinates the frontier, fetcher, extractor, and storage
    to perform a complete crawl.
    """

    def __init__(self, config: CrawlerConfig) -> None:
        """
        Initialize a crawl job.

        Args:
            config: Crawler configuration.
        """
        self.config = config

        # Generate IDs
        self.site_id = config.site_id or generate_site_id(config.seeds)
        self.run_id = generate_run_id()

        # Initialize components (lazy)
        self._storage: StorageBackend | None = None
        self._fetcher: Crawl4AIFetcher | None = None
        self._robots: RobotsChecker | None = None
        self._frontier: Frontier | None = None
        self._scheduler: DomainScheduler | None = None
        self._extractor: ContentExtractor | None = None
        self._quality_gate: QualityGate | None = None
        self._link_filter: LinkFilter | None = None

        # Tracking
        self._metrics = MetricsCollector()
        self._logger = CrawlLoggerAdapter(self.run_id, self.site_id)
        self._crawl_run: CrawlRun | None = None
        self._documents: list[Document] = []

    def _init_components(self) -> None:
        """Initialize all components."""
        # Storage
        self._storage = create_storage_backend(self.config.storage)
        self._storage.initialize()

        # Link filter
        self._link_filter = LinkFilter(
            allowed_domains=list(self.config.get_allowed_domains()),
            allow_subdomains=self.config.allow_subdomains,
            allowed_schemes=self.config.allowed_schemes,
            allowed_path_prefixes=self.config.allowed_path_prefixes,
            blocked_extensions=self.config.blocked_extensions,
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
            blocked_query_params=self.config.blocked_query_params,
        )

        # Frontier
        self._frontier = Frontier(
            run_id=self.run_id,
            site_id=self.site_id,
            link_filter=self._link_filter,
            max_depth=self.config.max_depth,
            max_pages=self.config.max_pages,
        )

        # Scheduler
        self._scheduler = DomainScheduler(
            config=self.config.rate_limit,
            max_concurrency=self.config.max_concurrency,
        )

        # Fetcher
        self._fetcher = Crawl4AIFetcher(
            fetch_mode=self.config.fetch_mode,
            user_agent=self.config.user_agent,
            timeout=self.config.http_timeout,
            browser_timeout=self.config.browser_timeout,
            headers=self.config.headers,
            cookies=self.config.cookies,
            proxy=self.config.proxy,
            retry_config=self.config.retry,
            follow_redirects=self.config.follow_redirects,
            max_redirects=self.config.max_redirects,
        )

        # Robots
        self._robots = RobotsChecker(
            mode=self.config.robots_mode,
            user_agent=self.config.user_agent,
            allowlist=self.config.robots_allowlist,
        )

        # Extractor
        self._extractor = ContentExtractor(
            allowed_domains=self.config.get_allowed_domains(),
        )

        # Quality gate
        qg_config = self.config.quality_gates
        self._quality_gate = QualityGate(
            min_text_length=qg_config.min_text_length,
            min_word_count=qg_config.min_word_count,
            max_duplicate_ratio=qg_config.max_duplicate_ratio,
            block_patterns=qg_config.block_patterns,
            detect_language=qg_config.detect_language,
            allowed_languages=qg_config.allowed_languages,
        )

    async def run(self) -> CrawlResult:
        """
        Execute the crawl job.

        Returns:
            CrawlResult with statistics and documents.
        """
        start_time = datetime.now()

        try:
            # Initialize
            self._init_components()

            # Create/update site record
            await self._save_site()

            # Create crawl run record
            self._crawl_run = CrawlRun(
                run_id=self.run_id,
                site_id=self.site_id,
                config_snapshot=self.config.model_dump(exclude={"on_page", "on_error", "on_change_detected", "redaction_hook"}),
                seeds=self.config.seeds,
            )
            self._crawl_run.mark_started()
            self._storage.save_run(self._crawl_run)

            self._logger.run_started(
                self.config.seeds,
                {"max_pages": self.config.max_pages, "max_depth": self.config.max_depth},
            )

            # Add seeds to frontier
            await self._frontier.add_seeds(self.config.seeds)

            # Main crawl loop
            await self._crawl_loop()

            # Finalize
            metrics = self._metrics.finalize()
            self._crawl_run.stats = CrawlStats(
                pages_discovered=metrics.pages_discovered,
                pages_crawled=metrics.pages_crawled,
                pages_failed=metrics.pages_failed,
                pages_skipped=metrics.pages_skipped,
                pages_changed=metrics.pages_changed,
                pages_new=metrics.pages_new,
                total_bytes_downloaded=metrics.total_bytes,
                total_fetch_time_ms=metrics.total_fetch_time_ms,
                total_extraction_time_ms=metrics.total_extraction_time_ms,
                avg_fetch_latency_ms=metrics.avg_fetch_latency_ms,
                status_codes=dict(metrics.status_codes),
                errors_by_type=dict(metrics.errors_by_type),
            )
            self._crawl_run.frontier_size = self._frontier.size
            self._crawl_run.max_depth_reached = self._frontier.max_depth_reached

            partial = metrics.pages_failed > 0
            self._crawl_run.mark_completed(partial=partial)
            self._storage.save_run(self._crawl_run)

            duration = (datetime.now() - start_time).total_seconds()
            self._logger.run_completed(metrics.to_dict(), duration)

            return CrawlResult(
                run_id=self.run_id,
                site_id=self.site_id,
                success=True,
                stats=self._crawl_run.stats,
                documents=self._documents,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error("Crawl job failed", error=str(e))

            if self._crawl_run:
                self._crawl_run.mark_failed(str(e))
                self._storage.save_run(self._crawl_run)

            self._logger.run_failed(str(e))

            return CrawlResult(
                run_id=self.run_id,
                site_id=self.site_id,
                success=False,
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        finally:
            # Cleanup
            if self._fetcher:
                await self._fetcher.close()
            if self._storage:
                self._storage.close()

    async def _crawl_loop(self) -> None:
        """Main crawl loop processing URLs from frontier."""
        while not self._frontier.is_empty:
            # Get batch of URLs
            items = await self._frontier.get_batch(self.config.max_concurrency)
            if not items:
                break

            # Process concurrently
            tasks = [self._process_url(item) for item in items]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Check limits
            if self._frontier.completed_count >= self.config.max_pages:
                logger.info("Max pages reached", count=self._frontier.completed_count)
                break

    async def _process_url(self, item: Any) -> None:
        """Process a single URL."""
        url = item.url
        domain = item.domain

        try:
            # Check robots.txt
            if not await self._robots.is_allowed(url):
                self._logger.page_skipped(url, "robots.txt blocked")
                self._metrics.record_skip("robots_blocked")
                await self._frontier.mark_failed(url, "robots.txt blocked")
                return

            # Acquire scheduler slot
            if not await self._scheduler.acquire(domain):
                # Circuit open, return to queue
                await self._frontier.return_to_queue(item)
                return

            try:
                # Fetch page
                fetch_result = await self._fetcher.fetch(url)

                self._metrics.record_fetch(
                    domain=domain,
                    status_code=fetch_result.status_code or 0,
                    latency_ms=fetch_result.latency_ms,
                    bytes_downloaded=fetch_result.content_length or 0,
                    success=fetch_result.is_success,
                )

                self._logger.page_fetched(
                    url,
                    fetch_result.status_code or 0,
                    fetch_result.latency_ms,
                    fetch_result.content_length,
                )

                if not fetch_result.is_success:
                    # Handle errors
                    if fetch_result.is_not_found:
                        await self._create_tombstone(url, item.depth, fetch_result.status_code or 404)
                    else:
                        self._logger.page_failed(url, fetch_result.error or "Unknown error")
                        self._metrics.record_error(
                            fetch_result.status.__class__.__name__, domain
                        )

                    self._scheduler.release(domain, success=False)
                    await self._frontier.mark_failed(url, fetch_result.error)
                    return

                # Extract content
                extraction = self._extractor.extract(
                    fetch_result,
                    fetch_result.final_url or url,
                    extract_html=self.config.extract_html,
                    extract_plain_text=self.config.extract_plain_text,
                )

                self._metrics.record_extraction(extraction.extraction_latency_ms)

                # Quality gate
                quality_result = self._quality_gate.check_all(
                    url,
                    extraction.markdown,
                    extraction.content_hash,
                )

                if not quality_result.passed:
                    self._logger.page_skipped(url, f"Quality: {quality_result.issue.value}")
                    self._metrics.record_skip(quality_result.issue.value)
                    self._scheduler.release(domain, success=True)
                    await self._frontier.mark_completed(url)
                    return

                # Create document
                document = await self._create_document(
                    url=url,
                    fetch_result=fetch_result,
                    extraction=extraction,
                    depth=item.depth,
                    referrer_url=item.referrer_url,
                )

                self._documents.append(document)

                # Call hook
                if self.config.on_page:
                    try:
                        self.config.on_page(document)
                    except Exception as e:
                        logger.warning("on_page hook error", error=str(e))

                # Add discovered links to frontier
                links_added = await self._frontier.add_batch(
                    extraction.internal_links,
                    depth=item.depth + 1,
                    referrer_url=url,
                )

                self._metrics.record_discovery(links_added)

                self._logger.page_extracted(
                    url,
                    len(extraction.markdown),
                    len(extraction.outlinks),
                    extraction.extraction_latency_ms,
                )

                self._scheduler.release(domain, success=True)
                await self._frontier.mark_completed(url)

            except Exception as e:
                self._scheduler.release(domain, success=False)
                raise

        except Exception as e:
            logger.error("Error processing URL", url=url, error=str(e))
            self._metrics.record_error(type(e).__name__, domain)
            await self._frontier.mark_failed(url, str(e))

            if self.config.on_error:
                try:
                    self.config.on_error(url, e)
                except Exception:
                    pass

    async def _create_document(
        self,
        url: str,
        fetch_result: Any,
        extraction: Any,
        depth: int,
        referrer_url: str | None,
    ) -> Document:
        """Create and save a document."""
        normalized_url = self._link_filter.normalizer.normalize(url)
        doc_id = compute_doc_id(normalized_url)
        now = datetime.now()

        # Check if page exists
        existing_page = self._storage.get_page(doc_id)
        is_new = existing_page is None

        # Check for content change
        content_changed = False
        if existing_page and existing_page.content_hash:
            if existing_page.content_hash != extraction.content_hash:
                content_changed = True
                self._logger.content_changed(
                    url, existing_page.content_hash, extraction.content_hash
                )

        if is_new:
            self._metrics.record_change(is_new=True)
        elif content_changed:
            self._metrics.record_change(is_new=False)
        else:
            self._metrics.record_unchanged()

        # Create version
        version_id = generate_version_id(extraction.content_hash)

        # Apply redaction if configured
        markdown = extraction.markdown
        if self.config.redaction_hook:
            try:
                markdown = self.config.redaction_hook(markdown)
            except Exception as e:
                logger.warning("Redaction hook error", error=str(e))

        version = PageVersion(
            version_id=version_id,
            page_id=doc_id,
            site_id=self.site_id,
            run_id=self.run_id,
            markdown=markdown,
            html=extraction.html,
            plain_text=extraction.plain_text,
            content_hash=extraction.content_hash,
            raw_hash=extraction.raw_hash,
            url=normalized_url,
            canonical_url=extraction.metadata.canonical_url,
            title=extraction.metadata.title,
            description=extraction.metadata.description,
            content_type=fetch_result.content_type,
            status_code=fetch_result.status_code or 200,
            language=extraction.metadata.language,
            headings_outline=[
                {"level": h.level, "text": h.text, "anchor": h.anchor}
                for h in extraction.metadata.headings_outline
            ],
            word_count=extraction.metadata.word_count,
            char_count=extraction.metadata.char_count,
            outlinks=extraction.outlinks,
            internal_link_count=len(extraction.internal_links),
            external_link_count=len(extraction.external_links),
            etag=fetch_result.etag,
            last_modified=fetch_result.last_modified,
            crawled_at=now,
            fetch_latency_ms=fetch_result.latency_ms,
            extraction_latency_ms=extraction.extraction_latency_ms,
        )

        self._storage.save_version(version)

        # Update page
        page = Page(
            page_id=doc_id,
            site_id=self.site_id,
            url=normalized_url,
            canonical_url=extraction.metadata.canonical_url,
            current_version_id=version_id,
            content_hash=extraction.content_hash,
            etag=fetch_result.etag,
            last_modified=fetch_result.last_modified,
            first_seen=existing_page.first_seen if existing_page else now,
            last_seen=now,
            last_crawled=now,
            last_changed=now if (is_new or content_changed) else (existing_page.last_changed if existing_page else now),
            depth=min(depth, existing_page.depth if existing_page else depth),
            referrer_url=referrer_url or (existing_page.referrer_url if existing_page else None),
            status_code=fetch_result.status_code,
            version_count=(existing_page.version_count if existing_page else 0) + 1,
        )

        self._storage.save_page(page)

        # Create document model
        document = Document(
            doc_id=doc_id,
            page_id=doc_id,
            version_id=version_id,
            source_url=url,
            normalized_url=normalized_url,
            canonical_url=extraction.metadata.canonical_url,
            markdown=markdown,
            html=extraction.html,
            plain_text=extraction.plain_text,
            title=extraction.metadata.title,
            description=extraction.metadata.description,
            content_type=fetch_result.content_type,
            status_code=fetch_result.status_code or 200,
            language=extraction.metadata.language,
            headings_outline=[
                HeadingInfo(level=h.level, text=h.text, anchor=h.anchor)
                for h in extraction.metadata.headings_outline
            ],
            depth=depth,
            referrer_url=referrer_url,
            run_id=self.run_id,
            site_id=self.site_id,
            first_seen=page.first_seen,
            last_seen=now,
            last_crawled=now,
            last_changed=page.last_changed,
            outlinks=extraction.outlinks,
            diagnostics=DocumentDiagnostics(
                fetch_latency_ms=fetch_result.latency_ms,
                extraction_latency_ms=extraction.extraction_latency_ms,
                raw_html_size=len(fetch_result.html) if fetch_result.html else None,
                extracted_text_size=len(markdown),
                link_count=len(extraction.outlinks),
            ),
        )

        # Trigger change callback
        if content_changed and self.config.on_change_detected:
            try:
                self.config.on_change_detected(document, existing_page)
            except Exception as e:
                logger.warning("on_change_detected hook error", error=str(e))

        return document

    async def _create_tombstone(
        self, url: str, depth: int, status_code: int
    ) -> None:
        """Create a tombstone for a deleted page."""
        normalized_url = self._link_filter.normalizer.normalize(url)
        doc_id = compute_doc_id(normalized_url)
        now = datetime.now()

        existing_page = self._storage.get_page(doc_id)

        if existing_page and not existing_page.is_tombstone:
            # Create tombstone version
            version_id = generate_version_id("tombstone", now)

            version = PageVersion(
                version_id=version_id,
                page_id=doc_id,
                site_id=self.site_id,
                run_id=self.run_id,
                markdown="",
                content_hash="tombstone",
                url=normalized_url,
                status_code=status_code,
                crawled_at=now,
                is_tombstone=True,
            )

            self._storage.save_version(version)

            # Update page as tombstone
            existing_page.is_tombstone = True
            existing_page.status_code = status_code
            existing_page.last_crawled = now
            existing_page.current_version_id = version_id

            self._storage.save_page(existing_page)

            self._logger.tombstone_created(url, status_code)
            self._metrics.record_deletion()

    async def _save_site(self) -> None:
        """Save or update site record."""
        existing = self._storage.get_site(self.site_id)

        if existing:
            existing.updated_at = datetime.now()
            existing.total_runs += 1
            self._storage.save_site(existing)
        else:
            site = Site(
                site_id=self.site_id,
                name=self.config.site_name or self.config.seeds[0],
                seeds=self.config.seeds,
                allowed_domains=list(self.config.get_allowed_domains()),
                allowed_subdomains=self.config.allow_subdomains,
                config=self.config.model_dump(exclude={"on_page", "on_error", "on_change_detected", "redaction_hook"}),
            )
            self._storage.save_site(site)

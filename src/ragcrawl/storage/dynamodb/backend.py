"""DynamoDB storage backend implementation."""

from datetime import datetime
from typing import Any

from ragcrawl.config.storage_config import DynamoDBConfig
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus
from ragcrawl.models.frontier_item import FrontierItem, FrontierStatus
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site
from ragcrawl.storage.backend import StorageBackend
from ragcrawl.storage.dynamodb.models import (
    CrawlRunModel,
    FrontierItemModel,
    PageModel,
    PageVersionModel,
    SiteModel,
)
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


class DynamoDBBackend(StorageBackend):
    """
    DynamoDB storage backend implementation using PynamoDB.
    """

    def __init__(self, config: DynamoDBConfig) -> None:
        """
        Initialize DynamoDB backend.

        Args:
            config: DynamoDB configuration.
        """
        self.config = config
        self._configure_models()

    def _configure_models(self) -> None:
        """Configure PynamoDB models with settings from config."""
        # Set region and endpoint for all models
        for model_class in [
            SiteModel,
            CrawlRunModel,
            PageModel,
            PageVersionModel,
            FrontierItemModel,
        ]:
            model_class.Meta.region = self.config.region
            model_class.Meta.table_name = f"{self.config.table_prefix}-{model_class.Meta.table_name.split('-')[-1]}"

            if self.config.endpoint_url:
                model_class.Meta.host = self.config.endpoint_url

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        for model_class in [
            SiteModel,
            CrawlRunModel,
            PageModel,
            PageVersionModel,
            FrontierItemModel,
        ]:
            if not model_class.exists():
                model_class.create_table(
                    read_capacity_units=self.config.read_capacity_units,
                    write_capacity_units=self.config.write_capacity_units,
                    wait=True,
                )
                logger.info(f"Created table: {model_class.Meta.table_name}")

    def close(self) -> None:
        """Close connections (no-op for DynamoDB)."""
        pass

    def health_check(self) -> bool:
        """Check if DynamoDB is accessible."""
        try:
            # Try to describe one table
            SiteModel.exists()
            return True
        except Exception as e:
            logger.error("DynamoDB health check failed", error=str(e))
            return False

    # === Site operations ===

    def save_site(self, site: Site) -> None:
        """Save or update a site."""
        model = SiteModel(
            site_id=site.site_id,
            name=site.name,
            seeds=site.seeds,
            allowed_domains=site.allowed_domains,
            allowed_subdomains=site.allowed_subdomains,
            config=site.config,
            created_at=site.created_at,
            updated_at=site.updated_at,
            last_crawl_at=site.last_crawl_at,
            last_sync_at=site.last_sync_at,
            total_pages=site.total_pages,
            total_runs=site.total_runs,
            is_active=site.is_active,
        )
        model.save()

    def get_site(self, site_id: str) -> Site | None:
        """Get a site by ID."""
        try:
            model = SiteModel.get(site_id)
            return self._model_to_site(model)
        except SiteModel.DoesNotExist:
            return None

    def list_sites(self) -> list[Site]:
        """List all sites."""
        return [self._model_to_site(m) for m in SiteModel.scan()]

    def delete_site(self, site_id: str) -> bool:
        """Delete a site and all associated data."""
        try:
            # Delete associated data
            for item in FrontierItemModel.scan(FrontierItemModel.site_id == site_id):
                item.delete()
            for item in PageVersionModel.scan(PageVersionModel.site_id == site_id):
                item.delete()
            for item in PageModel.scan(PageModel.site_id == site_id):
                item.delete()
            for item in CrawlRunModel.scan(CrawlRunModel.site_id == site_id):
                item.delete()

            # Delete site
            site = SiteModel.get(site_id)
            site.delete()
            return True
        except Exception:
            return False

    def _model_to_site(self, model: SiteModel) -> Site:
        """Convert DynamoDB model to Site."""
        return Site(
            site_id=model.site_id,
            name=model.name,
            seeds=model.seeds or [],
            allowed_domains=model.allowed_domains or [],
            allowed_subdomains=model.allowed_subdomains,
            config=model.config or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_crawl_at=model.last_crawl_at,
            last_sync_at=model.last_sync_at,
            total_pages=model.total_pages or 0,
            total_runs=model.total_runs or 0,
            is_active=model.is_active,
        )

    # === CrawlRun operations ===

    def save_run(self, run: CrawlRun) -> None:
        """Save or update a crawl run."""
        model = CrawlRunModel(
            run_id=run.run_id,
            site_id=run.site_id,
            status=run.status.value,
            error_message=run.error_message,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            config_snapshot=run.config_snapshot,
            seeds=run.seeds,
            is_sync=run.is_sync,
            parent_run_id=run.parent_run_id,
            stats=run.stats.model_dump() if run.stats else None,
            frontier_size=run.frontier_size,
            max_depth_reached=run.max_depth_reached,
        )
        model.save()

    def get_run(self, run_id: str) -> CrawlRun | None:
        """Get a crawl run by ID."""
        try:
            model = CrawlRunModel.get(run_id)
            return self._model_to_run(model)
        except CrawlRunModel.DoesNotExist:
            return None

    def list_runs(
        self,
        site_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CrawlRun]:
        """List crawl runs for a site."""
        # Use GSI to query by site_id
        results = CrawlRunModel.site_index.query(
            site_id,
            scan_index_forward=False,
            limit=limit,
        )
        return [self._model_to_run(m) for m in results]

    def get_latest_run(self, site_id: str) -> CrawlRun | None:
        """Get the latest crawl run for a site."""
        results = list(CrawlRunModel.site_index.query(
            site_id,
            scan_index_forward=False,
            limit=1,
        ))
        return self._model_to_run(results[0]) if results else None

    def _model_to_run(self, model: CrawlRunModel) -> CrawlRun:
        """Convert DynamoDB model to CrawlRun."""
        stats_data = model.stats or {}
        return CrawlRun(
            run_id=model.run_id,
            site_id=model.site_id,
            status=RunStatus(model.status),
            error_message=model.error_message,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            config_snapshot=model.config_snapshot or {},
            seeds=model.seeds or [],
            is_sync=model.is_sync,
            parent_run_id=model.parent_run_id,
            stats=CrawlStats(**stats_data),
            frontier_size=model.frontier_size or 0,
            max_depth_reached=model.max_depth_reached or 0,
        )

    # === Page operations ===

    def save_page(self, page: Page) -> None:
        """Save or update a page."""
        model = PageModel(
            page_id=page.page_id,
            site_id=page.site_id,
            url=page.url,
            canonical_url=page.canonical_url,
            current_version_id=page.current_version_id,
            content_hash=page.content_hash,
            etag=page.etag,
            last_modified=page.last_modified,
            first_seen=page.first_seen,
            last_seen=page.last_seen,
            last_crawled=page.last_crawled,
            last_changed=page.last_changed,
            depth=page.depth,
            referrer_url=page.referrer_url,
            status_code=page.status_code,
            is_tombstone=page.is_tombstone,
            error_count=page.error_count,
            last_error=page.last_error,
            version_count=page.version_count,
        )
        model.save()

    def get_page(self, page_id: str) -> Page | None:
        """Get a page by ID."""
        try:
            model = PageModel.get(page_id)
            return self._model_to_page(model)
        except PageModel.DoesNotExist:
            return None

    def get_page_by_url(self, site_id: str, url: str) -> Page | None:
        """Get a page by normalized URL."""
        # Need to scan with filter - consider adding GSI for URL lookups
        for model in PageModel.scan((PageModel.site_id == site_id) & (PageModel.url == url)):
            return self._model_to_page(model)
        return None

    def list_pages(
        self,
        site_id: str,
        limit: int = 1000,
        offset: int = 0,
        include_tombstones: bool = False,
    ) -> list[Page]:
        """List pages for a site."""
        filter_condition = PageModel.site_id == site_id
        if not include_tombstones:
            filter_condition &= PageModel.is_tombstone == False

        results = PageModel.scan(filter_condition, limit=limit)
        return [self._model_to_page(m) for m in results]

    def get_pages_needing_recrawl(
        self,
        site_id: str,
        max_age_hours: float | None = None,
        limit: int = 1000,
    ) -> list[Page]:
        """Get pages that need to be re-crawled."""
        filter_condition = (PageModel.site_id == site_id) & (PageModel.is_tombstone == False)

        if max_age_hours is not None:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            filter_condition &= (PageModel.last_crawled < cutoff) | (PageModel.last_crawled == None)

        results = PageModel.scan(filter_condition, limit=limit)
        return [self._model_to_page(m) for m in results]

    def count_pages(self, site_id: str, include_tombstones: bool = False) -> int:
        """Count pages for a site."""
        filter_condition = PageModel.site_id == site_id
        if not include_tombstones:
            filter_condition &= PageModel.is_tombstone == False

        return PageModel.count(filter_condition)

    def _model_to_page(self, model: PageModel) -> Page:
        """Convert DynamoDB model to Page."""
        return Page(
            page_id=model.page_id,
            site_id=model.site_id,
            url=model.url,
            canonical_url=model.canonical_url,
            current_version_id=model.current_version_id,
            content_hash=model.content_hash,
            etag=model.etag,
            last_modified=model.last_modified,
            first_seen=model.first_seen,
            last_seen=model.last_seen,
            last_crawled=model.last_crawled,
            last_changed=model.last_changed,
            depth=model.depth,
            referrer_url=model.referrer_url,
            status_code=model.status_code,
            is_tombstone=model.is_tombstone,
            error_count=model.error_count or 0,
            last_error=model.last_error,
            version_count=model.version_count or 0,
        )

    # === PageVersion operations ===

    def save_version(self, version: PageVersion) -> None:
        """Save a page version."""
        model = PageVersionModel(
            version_id=version.version_id,
            page_id=version.page_id,
            site_id=version.site_id,
            run_id=version.run_id,
            markdown=version.markdown,
            html=version.html,
            plain_text=version.plain_text,
            content_hash=version.content_hash,
            raw_hash=version.raw_hash,
            url=version.url,
            canonical_url=version.canonical_url,
            title=version.title,
            description=version.description,
            content_type=version.content_type,
            status_code=version.status_code,
            language=version.language,
            headings_outline=version.headings_outline,
            word_count=version.word_count,
            char_count=version.char_count,
            outlinks=version.outlinks,
            internal_link_count=version.internal_link_count,
            external_link_count=version.external_link_count,
            etag=version.etag,
            last_modified_header=version.last_modified,
            crawled_at=version.crawled_at,
            created_at=version.created_at,
            fetch_latency_ms=version.fetch_latency_ms,
            extraction_latency_ms=version.extraction_latency_ms,
            is_tombstone=version.is_tombstone,
            extra=version.extra,
        )
        model.save()

    def get_version(self, version_id: str) -> PageVersion | None:
        """Get a page version by ID."""
        try:
            model = PageVersionModel.get(version_id)
            return self._model_to_version(model)
        except PageVersionModel.DoesNotExist:
            return None

    def get_current_version(self, page_id: str) -> PageVersion | None:
        """Get the current version for a page."""
        page = self.get_page(page_id)
        if page and page.current_version_id:
            return self.get_version(page.current_version_id)
        return None

    def list_versions(
        self,
        page_id: str,
        limit: int = 100,
    ) -> list[PageVersion]:
        """List versions for a page."""
        results = PageVersionModel.page_index.query(
            page_id,
            scan_index_forward=False,
            limit=limit,
        )
        return [self._model_to_version(m) for m in results]

    def _model_to_version(self, model: PageVersionModel) -> PageVersion:
        """Convert DynamoDB model to PageVersion."""
        return PageVersion(
            version_id=model.version_id,
            page_id=model.page_id,
            site_id=model.site_id,
            run_id=model.run_id,
            markdown=model.markdown,
            html=model.html,
            plain_text=model.plain_text,
            content_hash=model.content_hash,
            raw_hash=model.raw_hash,
            url=model.url,
            canonical_url=model.canonical_url,
            title=model.title,
            description=model.description,
            content_type=model.content_type,
            status_code=model.status_code,
            language=model.language,
            headings_outline=model.headings_outline or [],
            word_count=model.word_count or 0,
            char_count=model.char_count or 0,
            outlinks=model.outlinks or [],
            internal_link_count=model.internal_link_count or 0,
            external_link_count=model.external_link_count or 0,
            etag=model.etag,
            last_modified=model.last_modified_header,
            crawled_at=model.crawled_at,
            created_at=model.created_at,
            fetch_latency_ms=model.fetch_latency_ms,
            extraction_latency_ms=model.extraction_latency_ms,
            is_tombstone=model.is_tombstone,
            extra=model.extra or {},
        )

    # === FrontierItem operations ===

    def save_frontier_item(self, item: FrontierItem) -> None:
        """Save a frontier item."""
        model = FrontierItemModel(
            item_id=item.item_id,
            run_id=item.run_id,
            site_id=item.site_id,
            url=item.url,
            normalized_url=item.normalized_url,
            url_hash=item.url_hash,
            depth=item.depth,
            referrer_url=item.referrer_url,
            priority=item.priority,
            status=item.status.value,
            retry_count=item.retry_count,
            last_error=item.last_error,
            discovered_at=item.discovered_at,
            scheduled_at=item.scheduled_at,
            started_at=item.started_at,
            completed_at=item.completed_at,
            domain=item.domain,
        )
        model.save()

    def get_frontier_items(
        self,
        run_id: str,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[FrontierItem]:
        """Get frontier items for a run."""
        results = FrontierItemModel.run_index.query(
            run_id,
            scan_index_forward=False,
            limit=limit,
        )

        items = [self._model_to_frontier_item(m) for m in results]

        if status:
            items = [i for i in items if i.status.value == status]

        return items

    def update_frontier_status(
        self,
        item_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Update frontier item status."""
        try:
            model = FrontierItemModel.get(item_id)
            model.status = status
            if error:
                model.last_error = error
            model.completed_at = datetime.now()
            model.save()
        except FrontierItemModel.DoesNotExist:
            pass

    def clear_frontier(self, run_id: str) -> int:
        """Clear all frontier items for a run."""
        count = 0
        for item in FrontierItemModel.run_index.query(run_id):
            item.delete()
            count += 1
        return count

    def _model_to_frontier_item(self, model: FrontierItemModel) -> FrontierItem:
        """Convert DynamoDB model to FrontierItem."""
        return FrontierItem(
            item_id=model.item_id,
            run_id=model.run_id,
            site_id=model.site_id,
            url=model.url,
            normalized_url=model.normalized_url,
            url_hash=model.url_hash,
            depth=model.depth,
            referrer_url=model.referrer_url,
            priority=model.priority,
            status=FrontierStatus(model.status),
            retry_count=model.retry_count or 0,
            last_error=model.last_error,
            discovered_at=model.discovered_at,
            scheduled_at=model.scheduled_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            domain=model.domain,
        )

    # === Bulk operations ===

    def save_pages_bulk(self, pages: list[Page]) -> int:
        """Bulk save pages."""
        with PageModel.batch_write() as batch:
            for page in pages:
                model = PageModel(
                    page_id=page.page_id,
                    site_id=page.site_id,
                    url=page.url,
                    # ... other fields
                )
                batch.save(model)
        return len(pages)

    def save_versions_bulk(self, versions: list[PageVersion]) -> int:
        """Bulk save versions."""
        with PageVersionModel.batch_write() as batch:
            for version in versions:
                model = PageVersionModel(
                    version_id=version.version_id,
                    page_id=version.page_id,
                    # ... other fields
                )
                batch.save(model)
        return len(versions)

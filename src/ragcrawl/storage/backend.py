"""Storage backend protocol and factory."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ragcrawl.config.storage_config import (
    DuckDBConfig,
    DynamoDBConfig,
    StorageConfig,
    StorageType,
)
from ragcrawl.models.crawl_run import CrawlRun
from ragcrawl.models.frontier_item import FrontierItem
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All backends must implement this interface to ensure feature parity.
    """

    # === Site operations ===

    @abstractmethod
    def save_site(self, site: Site) -> None:
        """Save or update a site."""
        ...

    @abstractmethod
    def get_site(self, site_id: str) -> Site | None:
        """Get a site by ID."""
        ...

    @abstractmethod
    def list_sites(self) -> list[Site]:
        """List all sites."""
        ...

    @abstractmethod
    def delete_site(self, site_id: str) -> bool:
        """Delete a site and all associated data."""
        ...

    # === CrawlRun operations ===

    @abstractmethod
    def save_run(self, run: CrawlRun) -> None:
        """Save or update a crawl run."""
        ...

    @abstractmethod
    def get_run(self, run_id: str) -> CrawlRun | None:
        """Get a crawl run by ID."""
        ...

    @abstractmethod
    def list_runs(
        self,
        site_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CrawlRun]:
        """List crawl runs for a site."""
        ...

    @abstractmethod
    def get_latest_run(self, site_id: str) -> CrawlRun | None:
        """Get the latest crawl run for a site."""
        ...

    # === Page operations ===

    @abstractmethod
    def save_page(self, page: Page) -> None:
        """Save or update a page."""
        ...

    @abstractmethod
    def get_page(self, page_id: str) -> Page | None:
        """Get a page by ID."""
        ...

    @abstractmethod
    def get_page_by_url(self, site_id: str, url: str) -> Page | None:
        """Get a page by normalized URL."""
        ...

    @abstractmethod
    def list_pages(
        self,
        site_id: str,
        limit: int = 1000,
        offset: int = 0,
        include_tombstones: bool = False,
    ) -> list[Page]:
        """List pages for a site."""
        ...

    @abstractmethod
    def get_pages_needing_recrawl(
        self,
        site_id: str,
        max_age_hours: float | None = None,
        limit: int = 1000,
    ) -> list[Page]:
        """Get pages that need to be re-crawled."""
        ...

    @abstractmethod
    def count_pages(self, site_id: str, include_tombstones: bool = False) -> int:
        """Count pages for a site."""
        ...

    # === PageVersion operations ===

    @abstractmethod
    def save_version(self, version: PageVersion) -> None:
        """Save a page version."""
        ...

    @abstractmethod
    def get_version(self, version_id: str) -> PageVersion | None:
        """Get a page version by ID."""
        ...

    @abstractmethod
    def get_current_version(self, page_id: str) -> PageVersion | None:
        """Get the current version for a page."""
        ...

    @abstractmethod
    def list_versions(
        self,
        page_id: str,
        limit: int = 100,
    ) -> list[PageVersion]:
        """List versions for a page."""
        ...

    # === FrontierItem operations (for pause/resume) ===

    @abstractmethod
    def save_frontier_item(self, item: FrontierItem) -> None:
        """Save a frontier item."""
        ...

    @abstractmethod
    def get_frontier_items(
        self,
        run_id: str,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[FrontierItem]:
        """Get frontier items for a run."""
        ...

    @abstractmethod
    def update_frontier_status(
        self,
        item_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Update frontier item status."""
        ...

    @abstractmethod
    def clear_frontier(self, run_id: str) -> int:
        """Clear all frontier items for a run. Returns count deleted."""
        ...

    # === Bulk operations ===

    @abstractmethod
    def save_pages_bulk(self, pages: list[Page]) -> int:
        """Bulk save pages. Returns count saved."""
        ...

    @abstractmethod
    def save_versions_bulk(self, versions: list[PageVersion]) -> int:
        """Bulk save versions. Returns count saved."""
        ...

    # === Utility ===

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the storage backend (create tables, etc.)."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close any connections."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the backend is healthy/available."""
        ...


def create_storage_backend(config: StorageConfig) -> StorageBackend:
    """
    Create a storage backend from configuration.

    Falls back to DuckDB if the configured backend is unavailable
    and fail_if_unavailable is False.

    Args:
        config: Storage configuration.

    Returns:
        A StorageBackend instance.

    Raises:
        RuntimeError: If backend unavailable and fail_if_unavailable is True.
    """
    if config.storage_type == StorageType.DYNAMODB:
        try:
            from ragcrawl.storage.dynamodb.backend import DynamoDBBackend

            assert isinstance(config.backend, DynamoDBConfig)
            backend = DynamoDBBackend(config.backend)

            if backend.health_check():
                logger.info("Using DynamoDB storage backend")
                return backend
            else:
                raise RuntimeError("DynamoDB health check failed")

        except Exception as e:
            if config.fail_if_unavailable:
                raise RuntimeError(f"DynamoDB unavailable: {e}") from e

            logger.warning(
                "DynamoDB unavailable, falling back to DuckDB",
                error=str(e),
            )

    # Default to DuckDB
    from ragcrawl.storage.duckdb.backend import DuckDBBackend

    if isinstance(config.backend, DuckDBConfig):
        db_config = config.backend
    else:
        # Fallback config
        db_config = DuckDBConfig()

    logger.info("Using DuckDB storage backend", path=str(db_config.path))
    return DuckDBBackend(db_config)

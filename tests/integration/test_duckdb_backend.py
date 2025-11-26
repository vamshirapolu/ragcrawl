"""Integration tests for DuckDB storage backend."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus
from ragcrawl.models.frontier_item import FrontierItem, FrontierStatus
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site


class TestDuckDBBackend:
    """Integration tests for DuckDB backend."""

    def test_initialize_creates_tables(self, duckdb_backend) -> None:
        """Test that initialization creates all required tables."""
        # Backend is already initialized via fixture
        # Verify we can query tables without error
        sites = duckdb_backend.list_sites()
        assert isinstance(sites, list)

    def test_site_crud_operations(self, duckdb_backend, sample_site: Site) -> None:
        """Test site CRUD operations."""
        # Create
        duckdb_backend.save_site(sample_site)

        # Read
        retrieved = duckdb_backend.get_site(sample_site.site_id)
        assert retrieved is not None
        assert retrieved.site_id == sample_site.site_id
        assert retrieved.name == sample_site.name
        assert retrieved.seeds == sample_site.seeds

        # Update
        sample_site.name = "Updated Name"
        sample_site.total_pages = 50
        duckdb_backend.save_site(sample_site)

        retrieved = duckdb_backend.get_site(sample_site.site_id)
        assert retrieved.name == "Updated Name"
        assert retrieved.total_pages == 50

        # List
        sites = duckdb_backend.list_sites()
        assert len(sites) >= 1
        assert any(s.site_id == sample_site.site_id for s in sites)

    def test_crawl_run_crud_operations(
        self, duckdb_backend, sample_site: Site, sample_crawl_run: CrawlRun
    ) -> None:
        """Test crawl run CRUD operations."""
        # Create site first
        duckdb_backend.save_site(sample_site)

        # Create run
        duckdb_backend.save_run(sample_crawl_run)

        # Read
        retrieved = duckdb_backend.get_run(sample_crawl_run.run_id)
        assert retrieved is not None
        assert retrieved.run_id == sample_crawl_run.run_id
        assert retrieved.site_id == sample_crawl_run.site_id
        assert retrieved.status == RunStatus.PENDING

        # Update status
        sample_crawl_run.status = RunStatus.RUNNING
        sample_crawl_run.started_at = datetime.now(timezone.utc)
        duckdb_backend.save_run(sample_crawl_run)

        retrieved = duckdb_backend.get_run(sample_crawl_run.run_id)
        assert retrieved.status == RunStatus.RUNNING

        # List runs for site
        runs = duckdb_backend.list_runs(sample_site.site_id)
        assert len(runs) >= 1
        assert any(r.run_id == sample_crawl_run.run_id for r in runs)

    def test_page_crud_operations(
        self, duckdb_backend, sample_site: Site, sample_page: Page
    ) -> None:
        """Test page CRUD operations."""
        # Create site first
        duckdb_backend.save_site(sample_site)

        # Create page
        duckdb_backend.save_page(sample_page)

        # Read
        retrieved = duckdb_backend.get_page(sample_page.page_id)
        assert retrieved is not None
        assert retrieved.page_id == sample_page.page_id
        assert retrieved.url == sample_page.url

        # Update
        sample_page.status_code = 200
        sample_page.last_crawled = datetime.now(timezone.utc)
        duckdb_backend.save_page(sample_page)

        retrieved = duckdb_backend.get_page(sample_page.page_id)
        assert retrieved.status_code == 200

        # Get by URL
        retrieved = duckdb_backend.get_page_by_url(sample_site.site_id, sample_page.url)
        assert retrieved is not None
        assert retrieved.page_id == sample_page.page_id

        # List pages for site
        pages = duckdb_backend.list_pages(sample_site.site_id)
        assert len(pages) >= 1

    def test_page_version_crud_operations(
        self,
        duckdb_backend,
        sample_site: Site,
        sample_crawl_run: CrawlRun,
        sample_page: Page,
        sample_page_version: PageVersion,
    ) -> None:
        """Test page version CRUD operations."""
        # Create prerequisites
        duckdb_backend.save_site(sample_site)
        duckdb_backend.save_run(sample_crawl_run)
        duckdb_backend.save_page(sample_page)

        # Create version
        duckdb_backend.save_version(sample_page_version)

        # Read
        retrieved = duckdb_backend.get_version(sample_page_version.version_id)
        assert retrieved is not None
        assert retrieved.version_id == sample_page_version.version_id
        assert retrieved.markdown == sample_page_version.markdown

        # List versions for page
        versions = duckdb_backend.list_versions(sample_page.page_id)
        assert len(versions) >= 1

        # Get current version (requires page to have current_version_id set)
        # First update page with current_version_id
        sample_page.current_version_id = sample_page_version.version_id
        duckdb_backend.save_page(sample_page)

        current = duckdb_backend.get_current_version(sample_page.page_id)
        assert current is not None
        assert current.version_id == sample_page_version.version_id

    def test_frontier_operations(
        self, duckdb_backend, sample_site: Site, sample_crawl_run: CrawlRun
    ) -> None:
        """Test frontier item operations."""
        # Create prerequisites
        duckdb_backend.save_site(sample_site)
        duckdb_backend.save_run(sample_crawl_run)

        # Create frontier items
        items = []
        for i in range(5):
            item = FrontierItem(
                item_id=str(uuid4()),
                run_id=sample_crawl_run.run_id,
                site_id=sample_site.site_id,
                url=f"https://example.com/page{i}",
                normalized_url=f"https://example.com/page{i}",
                url_hash=f"hash{i}",
                depth=1,
                priority=i,
                status=FrontierStatus.PENDING,
                discovered_at=datetime.now(timezone.utc),
                domain="example.com",
            )
            items.append(item)
            duckdb_backend.save_frontier_item(item)

        # List pending items
        pending = duckdb_backend.get_frontier_items(
            sample_crawl_run.run_id, status=FrontierStatus.PENDING.value, limit=10
        )
        assert len(pending) == 5

        # Update status
        duckdb_backend.update_frontier_status(items[0].item_id, FrontierStatus.COMPLETED.value)

        pending = duckdb_backend.get_frontier_items(
            sample_crawl_run.run_id, status=FrontierStatus.PENDING.value, limit=10
        )
        assert len(pending) == 4

        # Get all items (no status filter)
        all_items = duckdb_backend.get_frontier_items(sample_crawl_run.run_id, limit=10)
        assert len(all_items) == 5

    def test_multiple_sites_isolation(self, duckdb_backend) -> None:
        """Test that data is isolated between sites."""
        # Create two sites
        site1 = Site(
            site_id=str(uuid4()),
            name="Site 1",
            seeds=["https://site1.com"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        site2 = Site(
            site_id=str(uuid4()),
            name="Site 2",
            seeds=["https://site2.com"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        duckdb_backend.save_site(site1)
        duckdb_backend.save_site(site2)

        # Create pages for each site
        page1 = Page(
            page_id=str(uuid4()),
            site_id=site1.site_id,
            url="https://site1.com/page",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            depth=1,
        )
        page2 = Page(
            page_id=str(uuid4()),
            site_id=site2.site_id,
            url="https://site2.com/page",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            depth=1,
        )

        duckdb_backend.save_page(page1)
        duckdb_backend.save_page(page2)

        # Verify isolation
        site1_pages = duckdb_backend.list_pages(site1.site_id)
        site2_pages = duckdb_backend.list_pages(site2.site_id)

        assert len(site1_pages) == 1
        assert len(site2_pages) == 1
        assert site1_pages[0].url == "https://site1.com/page"
        assert site2_pages[0].url == "https://site2.com/page"

    def test_tombstone_pages(self, duckdb_backend, sample_site: Site) -> None:
        """Test tombstone page handling."""
        duckdb_backend.save_site(sample_site)

        # Create a regular page
        page = Page(
            page_id=str(uuid4()),
            site_id=sample_site.site_id,
            url="https://example.com/deleted",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            depth=1,
            is_tombstone=False,
        )
        duckdb_backend.save_page(page)

        # Mark as tombstone
        page.is_tombstone = True
        page.status_code = 404
        duckdb_backend.save_page(page)

        retrieved = duckdb_backend.get_page(page.page_id)
        # Check that tombstone flag is set (may be bool or truthy value)
        assert bool(retrieved.is_tombstone) is True
        assert retrieved.status_code == 404

    def test_crawl_run_statistics(
        self, duckdb_backend, sample_site: Site, sample_crawl_run: CrawlRun
    ) -> None:
        """Test crawl run statistics tracking."""
        duckdb_backend.save_site(sample_site)
        duckdb_backend.save_run(sample_crawl_run)

        # Update statistics
        sample_crawl_run.stats = CrawlStats(
            pages_crawled=50,
            pages_failed=5,
            pages_skipped=10,
            pages_new=45,
            pages_changed=5,
            total_bytes_downloaded=1_000_000,
        )
        sample_crawl_run.status = RunStatus.COMPLETED
        sample_crawl_run.completed_at = datetime.now(timezone.utc)
        duckdb_backend.save_run(sample_crawl_run)

        retrieved = duckdb_backend.get_run(sample_crawl_run.run_id)
        assert retrieved.stats.pages_crawled == 50
        assert retrieved.stats.pages_failed == 5
        assert retrieved.status == RunStatus.COMPLETED

    def test_backend_close_and_reopen(self, storage_config) -> None:
        """Test that backend can be closed and reopened."""
        from ragcrawl.storage.backend import create_storage_backend

        # Create and initialize
        backend = create_storage_backend(storage_config)
        backend.initialize()

        # Create a site
        site = Site(
            site_id=str(uuid4()),
            name="Test",
            seeds=["https://example.com"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        backend.save_site(site)

        # Close
        backend.close()

        # Reopen
        backend2 = create_storage_backend(storage_config)
        backend2.initialize()

        # Verify data persisted
        retrieved = backend2.get_site(site.site_id)
        assert retrieved is not None
        assert retrieved.name == "Test"

        backend2.close()

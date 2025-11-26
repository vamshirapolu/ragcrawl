"""Pytest configuration and fixtures."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pytest

from ragcrawl.config.crawler_config import CrawlerConfig, FetchMode, RobotsMode
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.config.sync_config import SyncConfig
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus
from ragcrawl.models.document import Document
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site
from ragcrawl.storage.backend import create_storage_backend


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary DuckDB path."""
    return temp_dir / "test.duckdb"


@pytest.fixture
def storage_config(temp_db_path: Path) -> StorageConfig:
    """Create a test storage config."""
    return StorageConfig(backend=DuckDBConfig(path=str(temp_db_path)))


@pytest.fixture
def duckdb_backend(storage_config: StorageConfig):
    """Create an initialized DuckDB backend."""
    backend = create_storage_backend(storage_config)
    backend.initialize()
    yield backend
    backend.close()


@pytest.fixture
def sample_site() -> Site:
    """Create a sample site for testing."""
    return Site(
        site_id=str(uuid4()),
        name="Test Site",
        seeds=["https://example.com"],
        allowed_domains=["example.com"],
        allowed_subdomains=True,
        config={"max_pages": 100},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        total_pages=0,
        total_runs=0,
        is_active=True,
    )


@pytest.fixture
def sample_crawl_run(sample_site: Site) -> CrawlRun:
    """Create a sample crawl run for testing."""
    return CrawlRun(
        run_id=str(uuid4()),
        site_id=sample_site.site_id,
        status=RunStatus.PENDING,
        created_at=datetime.now(timezone.utc),
        config_snapshot={"max_pages": 100},
        seeds=["https://example.com"],
        stats=CrawlStats(),
    )


@pytest.fixture
def sample_page(sample_site: Site) -> Page:
    """Create a sample page for testing."""
    return Page(
        page_id=str(uuid4()),
        site_id=sample_site.site_id,
        url="https://example.com/page1",
        canonical_url="https://example.com/page1",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        depth=1,
    )


@pytest.fixture
def sample_page_version(sample_page: Page, sample_crawl_run: CrawlRun) -> PageVersion:
    """Create a sample page version for testing."""
    return PageVersion(
        version_id=str(uuid4()),
        page_id=sample_page.page_id,
        site_id=sample_page.site_id,
        run_id=sample_crawl_run.run_id,
        markdown="# Test Page\n\nThis is test content.",
        content_hash="abc123",
        url=sample_page.url,
        title="Test Page",
        description="A test page",
        content_type="text/html",
        status_code=200,
        word_count=5,
        char_count=35,
        crawled_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    now = datetime.now(timezone.utc)
    return Document(
        doc_id="doc123",
        page_id="doc123",
        source_url="https://example.com/page1",
        normalized_url="https://example.com/page1",
        markdown="# Test Page\n\nThis is test content.",
        title="Test Page",
        status_code=200,
        content_type="text/html",
        depth=0,
        run_id="run123",
        site_id="site123",
        first_seen=now,
        last_seen=now,
        last_crawled=now,
    )


@pytest.fixture
def crawler_config(temp_dir: Path, temp_db_path: Path) -> CrawlerConfig:
    """Create a test crawler config."""
    return CrawlerConfig(
        seeds=["https://example.com"],
        max_pages=10,
        max_depth=3,
        fetch_mode=FetchMode.HTTP,
        robots_mode=RobotsMode.OFF,
        storage=StorageConfig(backend=DuckDBConfig(path=str(temp_db_path))),
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir / "output"),
        ),
    )


@pytest.fixture
def sync_config(temp_db_path: Path, sample_site: Site) -> SyncConfig:
    """Create a test sync config."""
    return SyncConfig(
        site_id=sample_site.site_id,
        storage=StorageConfig(backend=DuckDBConfig(path=str(temp_db_path))),
    )

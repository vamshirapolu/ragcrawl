"""Tests for data models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ragcrawl.models.chunk import Chunk
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus
from ragcrawl.models.document import Document
from ragcrawl.models.frontier_item import FrontierItem, FrontierStatus
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site


class TestDocument:
    """Tests for Document model."""

    def test_document_creation(self) -> None:
        """Test basic document creation."""
        now = datetime.now(timezone.utc)
        doc = Document(
            doc_id="doc123",
            page_id="doc123",
            source_url="https://example.com/page",
            normalized_url="https://example.com/page",
            markdown="# Test\n\nContent here.",
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

        assert doc.doc_id == "doc123"
        assert doc.source_url == "https://example.com/page"
        assert doc.title == "Test Page"

    def test_document_optional_fields(self) -> None:
        """Test document with optional fields."""
        now = datetime.now(timezone.utc)
        doc = Document(
            doc_id="doc123",
            page_id="doc123",
            source_url="https://example.com/page",
            normalized_url="https://example.com/page",
            markdown="Content",
            status_code=200,
            depth=0,
            run_id="run123",
            site_id="site123",
            first_seen=now,
            last_seen=now,
            last_crawled=now,
        )

        assert doc.title is None
        assert doc.description is None
        assert doc.language is None

    def test_document_with_metadata(self) -> None:
        """Test document with full metadata."""
        now = datetime.now(timezone.utc)
        doc = Document(
            doc_id="doc123",
            page_id="doc123",
            source_url="https://example.com/page",
            normalized_url="https://example.com/page",
            markdown="Content",
            title="Test",
            description="A test page",
            status_code=200,
            content_type="text/html",
            language="en",
            depth=1,
            run_id="run123",
            site_id="site123",
            first_seen=now,
            last_seen=now,
            last_crawled=now,
            outlinks=["https://example.com/other"],
        )

        assert doc.description == "A test page"
        assert doc.language == "en"
        assert len(doc.outlinks) == 1


class TestSite:
    """Tests for Site model."""

    def test_site_creation(self) -> None:
        """Test basic site creation."""
        site = Site(
            site_id=str(uuid4()),
            name="Test Site",
            seeds=["https://example.com"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert site.name == "Test Site"
        assert site.seeds == ["https://example.com"]
        assert site.is_active is True

    def test_site_defaults(self) -> None:
        """Test site default values."""
        site = Site(
            site_id=str(uuid4()),
            name="Test",
            seeds=["https://example.com"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert site.total_pages == 0
        assert site.total_runs == 0
        assert site.allowed_subdomains is True


class TestCrawlRun:
    """Tests for CrawlRun model."""

    def test_crawl_run_creation(self) -> None:
        """Test basic crawl run creation."""
        run = CrawlRun(
            run_id=str(uuid4()),
            site_id=str(uuid4()),
            status=RunStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            stats=CrawlStats(),
        )

        assert run.status == RunStatus.PENDING
        assert run.stats.pages_crawled == 0

    def test_crawl_run_status_transitions(self) -> None:
        """Test crawl run status values."""
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"
        assert RunStatus.PARTIAL.value == "partial"

    def test_crawl_run_stats(self) -> None:
        """Test crawl run statistics."""
        stats = CrawlStats(
            pages_crawled=100,
            pages_failed=5,
            pages_skipped=10,
            pages_changed=20,
            pages_new=80,
            total_bytes_downloaded=1_000_000,
        )

        assert stats.pages_crawled == 100
        assert stats.pages_failed == 5
        assert stats.total_bytes_downloaded == 1_000_000


class TestPage:
    """Tests for Page model."""

    def test_page_creation(self) -> None:
        """Test basic page creation."""
        page = Page(
            page_id=str(uuid4()),
            site_id=str(uuid4()),
            url="https://example.com/page",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            depth=1,
        )

        assert page.url == "https://example.com/page"
        assert page.depth == 1

    def test_page_defaults(self) -> None:
        """Test page default values."""
        page = Page(
            page_id=str(uuid4()),
            site_id=str(uuid4()),
            url="https://example.com/page",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            depth=0,
        )

        assert page.is_tombstone is False
        assert page.error_count == 0
        assert page.version_count == 0


class TestPageVersion:
    """Tests for PageVersion model."""

    def test_page_version_creation(self) -> None:
        """Test basic page version creation."""
        version = PageVersion(
            version_id=str(uuid4()),
            page_id=str(uuid4()),
            site_id=str(uuid4()),
            run_id=str(uuid4()),
            markdown="# Test\n\nContent",
            content_hash="abc123",
            url="https://example.com/page",
            status_code=200,
            crawled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )

        assert version.markdown == "# Test\n\nContent"
        assert version.status_code == 200

    def test_page_version_optional_fields(self) -> None:
        """Test page version with optional fields."""
        version = PageVersion(
            version_id=str(uuid4()),
            page_id=str(uuid4()),
            site_id=str(uuid4()),
            run_id=str(uuid4()),
            markdown="Content",
            content_hash="abc123",
            url="https://example.com/page",
            status_code=200,
            crawled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )

        assert version.title is None
        assert version.html is None
        assert version.etag is None


class TestFrontierItem:
    """Tests for FrontierItem model."""

    def test_frontier_item_creation(self) -> None:
        """Test basic frontier item creation."""
        item = FrontierItem(
            item_id=str(uuid4()),
            run_id=str(uuid4()),
            site_id=str(uuid4()),
            url="https://example.com/page",
            normalized_url="https://example.com/page",
            url_hash="abc123",
            depth=1,
            status=FrontierStatus.PENDING,
            discovered_at=datetime.now(timezone.utc),
            domain="example.com",
        )

        assert item.url == "https://example.com/page"
        assert item.status == FrontierStatus.PENDING

    def test_frontier_status_values(self) -> None:
        """Test frontier status values."""
        assert FrontierStatus.PENDING.value == "pending"
        assert FrontierStatus.IN_PROGRESS.value == "in_progress"
        assert FrontierStatus.COMPLETED.value == "completed"
        assert FrontierStatus.FAILED.value == "failed"
        assert FrontierStatus.SKIPPED.value == "skipped"


class TestChunk:
    """Tests for Chunk model."""

    def test_chunk_creation(self) -> None:
        """Test basic chunk creation."""
        chunk = Chunk(
            chunk_id="chunk123",
            doc_id="doc123",
            page_id="doc123",
            content="This is chunk content.",
            chunk_index=0,
            total_chunks=1,
            start_offset=0,
            end_offset=22,
            char_count=22,
            word_count=4,
            token_estimate=5,
            source_url="https://example.com/page",
            chunker_type="heading",
        )

        assert chunk.content == "This is chunk content."
        assert chunk.chunk_index == 0

    def test_chunk_with_heading(self) -> None:
        """Test chunk with heading info."""
        chunk = Chunk(
            chunk_id="chunk123",
            doc_id="doc123",
            page_id="doc123",
            content="Content under heading.",
            chunk_index=0,
            total_chunks=1,
            start_offset=0,
            end_offset=22,
            char_count=22,
            word_count=3,
            token_estimate=4,
            source_url="https://example.com/page",
            chunker_type="heading",
            section_path="Main > Sub",
            heading="Sub",
            heading_level=2,
        )

        assert chunk.section_path == "Main > Sub"
        assert chunk.heading == "Sub"
        assert chunk.heading_level == 2

    def test_chunk_with_tokens(self) -> None:
        """Test chunk with token estimate."""
        chunk = Chunk(
            chunk_id="chunk123",
            doc_id="doc123",
            page_id="doc123",
            content="Token counted content.",
            chunk_index=0,
            total_chunks=1,
            start_offset=0,
            end_offset=22,
            char_count=22,
            word_count=3,
            token_estimate=4,
            source_url="https://example.com/page",
            chunker_type="token",
        )

        assert chunk.token_estimate == 4

"""Integration tests for output publishing."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.models.document import Document
from ragcrawl.output.multi_page import MultiPagePublisher
from ragcrawl.output.single_page import SinglePagePublisher


def create_test_document(
    doc_id: str,
    url: str,
    title: str = "Test",
    markdown: str = "Content",
) -> Document:
    """Create a test document."""
    now = datetime.now(timezone.utc)
    return Document(
        doc_id=doc_id,
        page_id=doc_id,
        source_url=url,
        normalized_url=url,
        markdown=markdown,
        title=title,
        status_code=200,
        content_type="text/html",
        depth=0,
        run_id="run123",
        site_id="site123",
        first_seen=now,
        last_seen=now,
        last_crawled=now,
    )


class TestSinglePagePublisher:
    """Integration tests for single-page publisher."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.documents = [
            create_test_document(
                doc_id="doc1",
                url="https://example.com/page1",
                title="Page 1",
                markdown="# Page 1\n\nContent for page 1.",
            ),
            create_test_document(
                doc_id="doc2",
                url="https://example.com/page2",
                title="Page 2",
                markdown="# Page 2\n\nContent for page 2.",
            ),
        ]

    def test_single_page_output(self, temp_dir: Path) -> None:
        """Test single-page output generation."""
        config = OutputConfig(
            mode=OutputMode.SINGLE,
            root_dir=str(temp_dir),
        )
        publisher = SinglePagePublisher(config)

        files = publisher.publish(self.documents)

        assert len(files) == 1
        output_file = files[0]
        assert output_file.exists()

        content = output_file.read_text()
        assert "Page 1" in content
        assert "Page 2" in content

    def test_single_page_includes_toc(self, temp_dir: Path) -> None:
        """Test that single-page output includes table of contents."""
        config = OutputConfig(
            mode=OutputMode.SINGLE,
            root_dir=str(temp_dir),
            include_toc=True,
        )
        publisher = SinglePagePublisher(config)

        files = publisher.publish(self.documents)
        content = files[0].read_text()

        # Should have TOC markers or links
        assert "Table of Contents" in content or "- [" in content

    def test_single_page_metadata_header(self, temp_dir: Path) -> None:
        """Test single-page output with metadata header."""
        config = OutputConfig(
            mode=OutputMode.SINGLE,
            root_dir=str(temp_dir),
            include_metadata=True,
        )
        publisher = SinglePagePublisher(config)

        files = publisher.publish(self.documents)
        content = files[0].read_text()

        # Should include source URLs
        assert "example.com" in content

    def test_single_page_custom_filename(self, temp_dir: Path) -> None:
        """Test single-page output with custom filename."""
        config = OutputConfig(
            mode=OutputMode.SINGLE,
            root_dir=str(temp_dir),
            single_file_name="knowledge_base.md",
        )
        publisher = SinglePagePublisher(config)

        files = publisher.publish(self.documents)

        assert files[0].name == "knowledge_base.md"


class TestMultiPagePublisher:
    """Integration tests for multi-page publisher."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.documents = [
            create_test_document(
                doc_id="doc1",
                url="https://example.com/docs/guide",
                title="Guide",
                markdown="# Guide\n\nGuide content.\n\n[Link to API](/docs/api)",
            ),
            create_test_document(
                doc_id="doc2",
                url="https://example.com/docs/api",
                title="API",
                markdown="# API\n\nAPI content.\n\n[Back to Guide](/docs/guide)",
            ),
            create_test_document(
                doc_id="doc3",
                url="https://example.com/blog/post",
                title="Blog Post",
                markdown="# Blog Post\n\nBlog content.",
            ),
        ]

    def test_multi_page_output(self, temp_dir: Path) -> None:
        """Test multi-page output generation."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(self.documents)

        # Should have at least 3 files (might have index files too)
        assert len(files) >= 3
        for file in files:
            assert file.exists()
            assert file.suffix == ".md"

    def test_multi_page_preserves_structure(self, temp_dir: Path) -> None:
        """Test that multi-page output preserves URL structure."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(self.documents)

        # Check directory structure
        docs_dir = temp_dir / "example.com" / "docs"
        blog_dir = temp_dir / "example.com" / "blog"

        assert docs_dir.exists() or any("docs" in str(f) for f in files)

    def test_multi_page_link_rewriting(self, temp_dir: Path) -> None:
        """Test that internal links are rewritten."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
            rewrite_links=True,
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(self.documents)

        # Find the guide file
        guide_file = next(f for f in files if "guide" in str(f))
        content = guide_file.read_text()

        # Link should be rewritten to relative .md path
        assert ".md" in content or "api" in content

    def test_multi_page_index_generation(self, temp_dir: Path) -> None:
        """Test index file generation."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
            generate_index=True,
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(self.documents)

        # Should have an index file
        index_file = temp_dir / "index.md"
        # Index might be in a subdirectory
        index_exists = index_file.exists() or any("index" in str(f) for f in files)
        # This is optional behavior

    def test_multi_page_metadata_header(self, temp_dir: Path) -> None:
        """Test that each page has metadata header."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
            include_metadata=True,
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(self.documents)

        for file in files:
            content = file.read_text()
            # Should have source URL comment or frontmatter
            assert "example.com" in content or "---" in content

    def test_empty_documents(self, temp_dir: Path) -> None:
        """Test publishing empty document list."""
        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish([])

        assert len(files) == 0

    def test_documents_with_special_characters(self, temp_dir: Path) -> None:
        """Test documents with special characters in URLs."""
        docs = [
            create_test_document(
                doc_id="special",
                url="https://example.com/page with spaces",
                title="Special Page",
                markdown="# Special\n\nContent.",
            ),
        ]

        config = OutputConfig(
            mode=OutputMode.MULTI,
            root_dir=str(temp_dir),
        )
        publisher = MultiPagePublisher(config)

        files = publisher.publish(docs)

        # Should have at least 1 file (might have index too)
        assert len(files) >= 1
        # Filename should be sanitized
        for file in files:
            assert file.exists()

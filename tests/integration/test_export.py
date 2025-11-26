"""Integration tests for export functionality."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ragcrawl.export.json_exporter import JSONExporter, JSONLExporter
from ragcrawl.models.document import Document


def create_test_document(doc_id: str, title: str = "Test", markdown: str = "Content") -> Document:
    """Create a test document."""
    now = datetime.now(timezone.utc)
    return Document(
        doc_id=doc_id,
        page_id=doc_id,
        source_url=f"https://example.com/{doc_id}",
        normalized_url=f"https://example.com/{doc_id}",
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


class TestJSONExporter:
    """Integration tests for JSON exporter."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.documents = [
            create_test_document(
                doc_id=f"doc{i}",
                title=f"Page {i}",
                markdown=f"# Page {i}\n\nContent for page {i}.",
            )
            for i in range(3)
        ]

    def test_export_to_json(self, temp_dir: Path) -> None:
        """Test exporting documents to JSON file."""
        exporter = JSONExporter()
        output_path = temp_dir / "output.json"

        exporter.export_documents(self.documents, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["doc_id"] == "doc0"
        assert data[0]["source_url"] == "https://example.com/doc0"

    def test_export_json_formatting(self, temp_dir: Path) -> None:
        """Test JSON export formatting."""
        exporter = JSONExporter(indent=2)
        output_path = temp_dir / "formatted.json"

        exporter.export_documents(self.documents, output_path)

        content = output_path.read_text()
        # Should be formatted with newlines
        assert "\n" in content

    def test_export_json_compact(self, temp_dir: Path) -> None:
        """Test compact JSON export."""
        exporter = JSONExporter(indent=None)
        output_path = temp_dir / "compact.json"

        exporter.export_documents(self.documents, output_path)

        content = output_path.read_text()
        # Should be single line (no indentation newlines)
        lines = content.strip().split("\n")
        assert len(lines) == 1

    def test_export_empty_list(self, temp_dir: Path) -> None:
        """Test exporting empty document list."""
        exporter = JSONExporter()
        output_path = temp_dir / "empty.json"

        exporter.export_documents([], output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert data == []


class TestJSONLExporter:
    """Integration tests for JSONL exporter."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.documents = [
            create_test_document(
                doc_id=f"doc{i}",
                title=f"Page {i}",
                markdown=f"# Page {i}\n\nContent for page {i}.",
            )
            for i in range(3)
        ]

    def test_export_to_jsonl(self, temp_dir: Path) -> None:
        """Test exporting documents to JSONL file."""
        exporter = JSONLExporter()
        output_path = temp_dir / "output.jsonl"

        exporter.export_documents(self.documents, output_path)

        assert output_path.exists()

        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == 3

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["doc_id"] == f"doc{i}"

    def test_export_jsonl_streaming(self, temp_dir: Path) -> None:
        """Test JSONL streaming export."""
        exporter = JSONLExporter()
        output_path = temp_dir / "stream.jsonl"

        # Export large number of documents
        many_docs = [
            create_test_document(
                doc_id=f"doc{i}",
                markdown=f"Content {i}",
            )
            for i in range(100)
        ]

        exporter.export_documents(many_docs, output_path)

        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == 100

    def test_export_empty_jsonl(self, temp_dir: Path) -> None:
        """Test exporting empty list to JSONL."""
        exporter = JSONLExporter()
        output_path = temp_dir / "empty.jsonl"

        exporter.export_documents([], output_path)

        content = output_path.read_text()
        assert content == ""

    def test_jsonl_unicode_content(self, temp_dir: Path) -> None:
        """Test JSONL export with unicode content."""
        docs = [
            create_test_document(
                doc_id="unicode",
                title="Unicode Test 🌍",
                markdown="Hello, 世界! 🚀",
            )
        ]

        exporter = JSONLExporter()
        output_path = temp_dir / "unicode.jsonl"

        exporter.export_documents(docs, output_path)

        line = output_path.read_text().strip()
        data = json.loads(line)
        assert data["title"] == "Unicode Test 🌍"
        assert "世界" in data["markdown"]

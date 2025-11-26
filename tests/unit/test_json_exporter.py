"""Tests for JSON and JSONL exporters."""

from datetime import datetime, timezone

import pytest

from ragcrawl.export.json_exporter import JSONExporter, JSONLExporter
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document, DocumentDiagnostics


def make_document() -> Document:
    """Create a sample document with diagnostics and HTML."""
    now = datetime.now(timezone.utc)
    return Document(
        doc_id="doc1",
        page_id="doc1",
        version_id="v1",
        source_url="https://example.com/page",
        normalized_url="https://example.com/page",
        canonical_url="https://example.com/page",
        markdown="# Title\n\nBody text",
        html="<p>Body text</p>",
        plain_text="Body text",
        title="My Page",
        description="Description",
        content_type="text/html",
        status_code=200,
        language="en",
        depth=0,
        run_id="run1",
        site_id="site1",
        first_seen=now,
        last_seen=now,
        last_crawled=now,
        outlinks=[],
        diagnostics=DocumentDiagnostics(
            fetch_latency_ms=1.2,
            extraction_latency_ms=2.3,
            raw_html_size=100,
            extracted_text_size=80,
            link_count=3,
        ),
    )


def test_json_exporter_includes_optional_fields(tmp_path) -> None:
    """Export document to string and file with optional fields included."""
    doc = make_document()
    exporter = JSONExporter(include_html=True, include_diagnostics=True, indent=None)

    json_str = exporter.export_document(doc)
    assert '"html":' in json_str
    assert '"diagnostics":' in json_str

    out_file = tmp_path / "doc.json"
    result = exporter.export_document(doc, path=out_file)
    assert result is None
    assert out_file.exists() and out_file.read_text()


def test_jsonl_exporter_streams_lines(tmp_path) -> None:
    """Export multiple documents/chunks to JSONL file."""
    doc1 = make_document()
    doc2 = make_document()
    doc2.doc_id = "doc2"
    doc2.normalized_url = "https://example.com/other"

    exporter = JSONLExporter(include_html=False, include_diagnostics=False)
    out_docs = tmp_path / "docs.jsonl"
    exporter.export_documents([doc1, doc2], out_docs)
    lines = out_docs.read_text().strip().splitlines()
    assert len(lines) == 2
    assert '"html"' not in lines[0]

    chunk = Chunk(
        chunk_id="c1",
        doc_id="doc1",
        page_id="doc1",
        version_id="v1",
        content="chunk content",
        content_type="markdown",
        chunk_index=0,
        total_chunks=1,
        start_offset=0,
        end_offset=12,
        char_count=12,
        word_count=2,
        token_estimate=3,
        section_path=None,
        heading=None,
        heading_level=None,
        source_url=doc1.source_url,
        title=doc1.title,
        chunker_type="token",
        overlap_tokens=0,
    )
    chunk_path = tmp_path / "chunks.jsonl"
    exporter.export_chunks([chunk], chunk_path)
    chunk_lines = chunk_path.read_text().strip().splitlines()
    assert len(chunk_lines) == 1
    assert '"chunk_id": "c1"' in chunk_lines[0]


def test_json_serializer_rejects_unknown_types() -> None:
    """Custom serializer raises TypeError for unsupported objects."""
    with pytest.raises(TypeError):
        JSONExporter._json_serializer(object())


def test_json_exporter_excludes_optional_fields_by_default() -> None:
    """When include flags are false, optional sections are omitted."""
    doc = make_document()
    exporter = JSONExporter(include_html=False, include_diagnostics=False, indent=2)
    rendered = exporter.export_document(doc)
    assert '"html"' not in rendered
    assert '"diagnostics"' not in rendered

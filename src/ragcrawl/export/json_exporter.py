"""JSON and JSONL exporters."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ragcrawl.export.exporter import Exporter
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document


class JSONExporter(Exporter):
    """
    Exports documents and chunks as JSON.
    """

    def __init__(
        self,
        indent: int | None = 2,
        include_html: bool = False,
        include_diagnostics: bool = True,
    ) -> None:
        """
        Initialize JSON exporter.

        Args:
            indent: JSON indentation (None for compact).
            include_html: Include HTML content in export.
            include_diagnostics: Include diagnostic info.
        """
        self.indent = indent
        self.include_html = include_html
        self.include_diagnostics = include_diagnostics

    def export_document(
        self, document: Document, path: Path | None = None
    ) -> str | None:
        """Export a document as JSON."""
        data = self._document_to_dict(document)
        json_str = json.dumps(data, indent=self.indent, default=self._json_serializer)

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str)
            return None

        return json_str

    def export_documents(self, documents: list[Document], path: Path) -> None:
        """Export documents as JSON array."""
        data = [self._document_to_dict(doc) for doc in documents]
        json_str = json.dumps(data, indent=self.indent, default=self._json_serializer)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str)

    def export_chunk(self, chunk: Chunk, path: Path | None = None) -> str | None:
        """Export a chunk as JSON."""
        data = self._chunk_to_dict(chunk)
        json_str = json.dumps(data, indent=self.indent, default=self._json_serializer)

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str)
            return None

        return json_str

    def export_chunks(self, chunks: list[Chunk], path: Path) -> None:
        """Export chunks as JSON array."""
        data = [self._chunk_to_dict(chunk) for chunk in chunks]
        json_str = json.dumps(data, indent=self.indent, default=self._json_serializer)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str)

    def _document_to_dict(self, document: Document) -> dict[str, Any]:
        """Convert document to dictionary."""
        data = {
            "doc_id": document.doc_id,
            "page_id": document.page_id,
            "version_id": document.version_id,
            "source_url": document.source_url,
            "normalized_url": document.normalized_url,
            "canonical_url": document.canonical_url,
            "title": document.title,
            "description": document.description,
            "markdown": document.markdown,
            "content_type": document.content_type,
            "status_code": document.status_code,
            "language": document.language,
            "depth": document.depth,
            "referrer_url": document.referrer_url,
            "run_id": document.run_id,
            "site_id": document.site_id,
            "first_seen": document.first_seen,
            "last_seen": document.last_seen,
            "last_crawled": document.last_crawled,
            "last_changed": document.last_changed,
            "outlinks": document.outlinks,
            "is_tombstone": document.is_tombstone,
            "headings_outline": [
                {"level": h.level, "text": h.text, "anchor": h.anchor}
                for h in document.headings_outline
            ],
        }

        if self.include_html and document.html:
            data["html"] = document.html

        if self.include_diagnostics:
            data["diagnostics"] = {
                "fetch_latency_ms": document.diagnostics.fetch_latency_ms,
                "extraction_latency_ms": document.diagnostics.extraction_latency_ms,
                "raw_html_size": document.diagnostics.raw_html_size,
                "extracted_text_size": document.diagnostics.extracted_text_size,
                "link_count": document.diagnostics.link_count,
            }

        return data

    def _chunk_to_dict(self, chunk: Chunk) -> dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "page_id": chunk.page_id,
            "version_id": chunk.version_id,
            "content": chunk.content,
            "content_type": chunk.content_type,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            "start_offset": chunk.start_offset,
            "end_offset": chunk.end_offset,
            "char_count": chunk.char_count,
            "word_count": chunk.word_count,
            "token_estimate": chunk.token_estimate,
            "section_path": chunk.section_path,
            "heading": chunk.heading,
            "heading_level": chunk.heading_level,
            "source_url": chunk.source_url,
            "title": chunk.title,
            "chunker_type": chunk.chunker_type,
            "overlap_tokens": chunk.overlap_tokens,
        }

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """JSON serializer for special types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class JSONLExporter(Exporter):
    """
    Exports documents and chunks as JSONL (one JSON object per line).

    JSONL is better for streaming and large datasets.
    """

    def __init__(
        self,
        include_html: bool = False,
        include_diagnostics: bool = True,
    ) -> None:
        """
        Initialize JSONL exporter.

        Args:
            include_html: Include HTML content.
            include_diagnostics: Include diagnostics.
        """
        self.include_html = include_html
        self.include_diagnostics = include_diagnostics
        self._json_exporter = JSONExporter(
            indent=None,
            include_html=include_html,
            include_diagnostics=include_diagnostics,
        )

    def export_document(
        self, document: Document, path: Path | None = None
    ) -> str | None:
        """Export a document as JSONL line."""
        return self._json_exporter.export_document(document, path)

    def export_documents(self, documents: list[Document], path: Path) -> None:
        """Export documents as JSONL file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            for doc in documents:
                line = self._json_exporter.export_document(doc)
                f.write(line + "\n")

    def export_chunk(self, chunk: Chunk, path: Path | None = None) -> str | None:
        """Export a chunk as JSONL line."""
        return self._json_exporter.export_chunk(chunk, path)

    def export_chunks(self, chunks: list[Chunk], path: Path) -> None:
        """Export chunks as JSONL file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            for chunk in chunks:
                line = self._json_exporter.export_chunk(chunk)
                f.write(line + "\n")

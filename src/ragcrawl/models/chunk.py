"""Chunk model for RAG-ready content segmentation."""

from typing import Any

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    Represents a chunk of content for RAG/embedding pipelines.

    Chunks are segments of a document optimized for vector embedding
    and retrieval, with metadata for context reconstruction.
    """

    # Identifiers
    chunk_id: str = Field(description="Unique chunk ID")
    doc_id: str = Field(description="Parent document ID")
    page_id: str = Field(description="Parent page ID (same as doc_id)")
    version_id: str | None = Field(default=None, description="Version ID of source content")

    # Content
    content: str = Field(description="Chunk text content")
    content_type: str = Field(default="markdown", description="Content type (markdown, text)")

    # Position in document
    chunk_index: int = Field(ge=0, description="Index of this chunk in document (0-based)")
    total_chunks: int = Field(ge=1, description="Total chunks in document")
    start_offset: int = Field(ge=0, description="Start character offset in source")
    end_offset: int = Field(ge=0, description="End character offset in source")

    # Size metrics
    char_count: int = Field(ge=0, description="Character count")
    word_count: int = Field(ge=0, description="Approximate word count")
    token_estimate: int = Field(ge=0, description="Estimated token count")

    # Structure context
    section_path: str | None = Field(
        default=None, description="Hierarchical section path (e.g., 'Introduction > Overview')"
    )
    heading: str | None = Field(
        default=None, description="Nearest heading above this chunk"
    )
    heading_level: int | None = Field(
        default=None, ge=1, le=6, description="Level of nearest heading"
    )

    # Source metadata (inherited from document)
    source_url: str = Field(description="URL of source page")
    title: str | None = Field(default=None, description="Page title")

    # Chunking metadata
    chunker_type: str = Field(description="Type of chunker used (heading, token, etc.)")
    overlap_tokens: int = Field(default=0, description="Tokens overlapping with previous chunk")

    # Extensible
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}

    @property
    def is_first(self) -> bool:
        """Check if this is the first chunk."""
        return self.chunk_index == 0

    @property
    def is_last(self) -> bool:
        """Check if this is the last chunk."""
        return self.chunk_index == self.total_chunks - 1

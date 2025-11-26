"""Document model representing a crawled page with rich metadata."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HeadingInfo(BaseModel):
    """Information about a heading in the document."""

    level: int = Field(ge=1, le=6, description="Heading level (1-6)")
    text: str = Field(description="Heading text content")
    anchor: str | None = Field(default=None, description="Anchor ID for the heading")


class DocumentDiagnostics(BaseModel):
    """Diagnostic information from crawling/extraction."""

    fetch_latency_ms: float | None = Field(default=None, description="Time to fetch the page in ms")
    extraction_latency_ms: float | None = Field(
        default=None, description="Time to extract content in ms"
    )
    raw_html_size: int | None = Field(default=None, description="Size of raw HTML in bytes")
    extracted_text_size: int | None = Field(
        default=None, description="Size of extracted text in bytes"
    )
    link_count: int | None = Field(default=None, description="Number of links found")
    image_count: int | None = Field(default=None, description="Number of images found")
    error_message: str | None = Field(default=None, description="Error message if any")
    retry_count: int = Field(default=0, description="Number of retries attempted")


class Document(BaseModel):
    """
    A crawled document with rich metadata for LLM/RAG consumption.

    This is the primary output model containing all extracted content
    and metadata from a crawled page.
    """

    # Stable identifiers
    doc_id: str = Field(description="Stable ID: hash(normalized_url)")
    page_id: str = Field(description="Alias for doc_id for compatibility")
    version_id: str | None = Field(default=None, description="Content hash for this version")

    # URLs
    source_url: str = Field(description="Original URL as discovered")
    normalized_url: str = Field(description="Normalized/canonical URL")
    canonical_url: str | None = Field(default=None, description="Canonical URL from page metadata")

    # Content
    markdown: str = Field(description="Extracted clean Markdown content")
    html: str | None = Field(default=None, description="Cleaned HTML (optional)")
    plain_text: str | None = Field(default=None, description="Plain text extraction (optional)")

    # Page metadata
    title: str | None = Field(default=None, description="Page title")
    description: str | None = Field(default=None, description="Meta description")
    content_type: str | None = Field(default=None, description="HTTP Content-Type")
    status_code: int = Field(description="HTTP status code")
    language: str | None = Field(default=None, description="Detected language")

    # Structure metadata
    headings_outline: list[HeadingInfo] = Field(
        default_factory=list, description="Hierarchical headings outline"
    )
    section_path: str | None = Field(
        default=None, description="Breadcrumb path in site structure"
    )

    # Crawl context
    depth: int = Field(ge=0, description="Crawl depth from seed")
    referrer_url: str | None = Field(default=None, description="URL that linked to this page")
    run_id: str = Field(description="ID of the crawl run")
    site_id: str = Field(description="ID of the site being crawled")

    # Timestamps
    first_seen: datetime = Field(description="When page was first discovered")
    last_seen: datetime = Field(description="When page was last seen in crawl")
    last_crawled: datetime = Field(description="When page was last fetched")
    last_changed: datetime | None = Field(
        default=None, description="When content last changed"
    )

    # Links extracted from this page
    outlinks: list[str] = Field(default_factory=list, description="URLs linked from this page")

    # Diagnostics
    diagnostics: DocumentDiagnostics = Field(
        default_factory=DocumentDiagnostics, description="Crawl diagnostics"
    )

    # Extensible metadata
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom metadata"
    )

    # Tombstone flag
    is_tombstone: bool = Field(
        default=False, description="True if page was deleted (404/410)"
    )

    model_config = {"frozen": False, "extra": "allow"}

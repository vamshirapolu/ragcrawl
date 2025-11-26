"""PageVersion model representing a specific version of page content."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PageVersion(BaseModel):
    """
    Represents a specific version of a page's content.

    Each time content changes, a new PageVersion is created.
    This enables version history and change tracking for KB updates.
    """

    # Identifiers
    version_id: str = Field(description="Unique version ID (content_hash or UUID)")
    page_id: str = Field(description="ID of the parent Page")
    site_id: str = Field(description="ID of the site")
    run_id: str = Field(description="ID of the crawl run that created this version")

    # Content
    markdown: str = Field(description="Extracted Markdown content")
    html: str | None = Field(default=None, description="Cleaned HTML (optional)")
    plain_text: str | None = Field(default=None, description="Plain text (optional)")

    # Content hashes for deduplication
    content_hash: str = Field(description="Hash of normalized markdown content")
    raw_hash: str | None = Field(default=None, description="Hash of raw HTML")

    # Page metadata snapshot
    url: str = Field(description="URL at time of crawl")
    canonical_url: str | None = Field(default=None, description="Canonical URL")
    title: str | None = Field(default=None, description="Page title")
    description: str | None = Field(default=None, description="Meta description")
    content_type: str | None = Field(default=None, description="HTTP Content-Type")
    status_code: int = Field(description="HTTP status code")
    language: str | None = Field(default=None, description="Detected language")

    # Structure metadata
    headings_outline: list[dict[str, Any]] = Field(
        default_factory=list, description="Headings structure"
    )
    word_count: int = Field(default=0, description="Word count of extracted text")
    char_count: int = Field(default=0, description="Character count of markdown")

    # Links snapshot
    outlinks: list[str] = Field(
        default_factory=list, description="URLs linked from this page"
    )
    internal_link_count: int = Field(default=0, description="Number of internal links")
    external_link_count: int = Field(default=0, description="Number of external links")

    # HTTP caching metadata
    etag: str | None = Field(default=None, description="ETag from response")
    last_modified: str | None = Field(default=None, description="Last-Modified header")

    # Timestamps
    crawled_at: datetime = Field(description="When this version was crawled")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When record was created"
    )

    # Diagnostics
    fetch_latency_ms: float | None = Field(default=None)
    extraction_latency_ms: float | None = Field(default=None)

    # Tombstone
    is_tombstone: bool = Field(
        default=False, description="True if this represents a deletion (404/410)"
    )

    # Extensible
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}

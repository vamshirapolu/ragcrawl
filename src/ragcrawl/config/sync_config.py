"""Configuration for incremental sync operations."""

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from ragcrawl.config.markdown_config import MarkdownConfig
from ragcrawl.config.output_config import OutputConfig
from ragcrawl.config.storage_config import StorageConfig


class SyncStrategy(str, Enum):
    """Strategy for detecting content changes."""

    SITEMAP = "sitemap"  # Use sitemap.xml lastmod
    HEADERS = "headers"  # Use ETag/Last-Modified conditional requests
    HASH = "hash"  # Content hash diffing
    ALL = "all"  # Try all strategies in order


class SyncConfig(BaseModel):
    """
    Configuration for incremental sync/update operations.

    Sync operations detect and process only changed content,
    minimizing redundant work and API calls.
    """

    # === Site identification ===
    site_id: str = Field(description="ID of the site to sync")

    # === Sync strategy ===
    strategy: list[SyncStrategy] = Field(
        default_factory=lambda: [SyncStrategy.SITEMAP, SyncStrategy.HEADERS, SyncStrategy.HASH],
        description="Sync strategies to try, in order of preference",
    )

    # === Sitemap options ===
    sitemap_urls: list[str] = Field(
        default_factory=list,
        description="Explicit sitemap URLs (auto-discovered if empty)",
    )
    respect_sitemap_lastmod: bool = Field(
        default=True,
        description="Skip pages with unchanged lastmod in sitemap",
    )

    # === Conditional request options ===
    use_etag: bool = Field(default=True, description="Use ETag for conditional requests")
    use_last_modified: bool = Field(
        default=True, description="Use Last-Modified for conditional requests"
    )

    # === Hash diffing options ===
    normalize_for_hash: bool = Field(
        default=True,
        description="Normalize content before hashing to reduce false positives",
    )
    hash_noise_patterns: list[str] = Field(
        default_factory=lambda: [
            r"\d{4}-\d{2}-\d{2}",  # Dates
            r"\d{1,2}:\d{2}(:\d{2})?",  # Times
            r"©\s*\d{4}",  # Copyright years
        ],
        description="Patterns to strip before hashing (noise reduction)",
    )

    # === Scope ===
    max_pages: int | None = Field(
        default=None, description="Maximum pages to sync (None = all)"
    )
    include_patterns: list[str] = Field(
        default_factory=list, description="Only sync URLs matching these patterns"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="Skip URLs matching these patterns"
    )
    max_age_hours: float | None = Field(
        default=None,
        description="Only re-check pages older than this (None = check all)",
    )

    # === Tombstone handling ===
    detect_deletions: bool = Field(
        default=True, description="Detect and mark deleted pages (404/410)"
    )
    deletion_threshold: int = Field(
        default=2,
        ge=1,
        description="Consecutive 404s before marking as deleted",
    )

    # === Storage ===
    storage: StorageConfig = Field(
        default_factory=StorageConfig, description="Storage backend configuration"
    )

    # === Output ===
    output: OutputConfig | None = Field(
        default=None, description="Output configuration (None = no file output)"
    )

    # === Markdown extraction ===
    markdown: MarkdownConfig = Field(
        default_factory=MarkdownConfig,
        description="Markdown generation and content filtering configuration",
    )

    # === Hooks ===
    on_page: Callable[..., Any] | None = Field(
        default=None, description="Callback on each page processed", exclude=True
    )
    on_change_detected: Callable[..., Any] | None = Field(
        default=None, description="Callback when content changes", exclude=True
    )
    on_deletion_detected: Callable[..., Any] | None = Field(
        default=None, description="Callback when page deletion detected", exclude=True
    )
    on_error: Callable[..., Any] | None = Field(
        default=None, description="Callback on errors", exclude=True
    )

    model_config = {"frozen": False, "extra": "allow"}

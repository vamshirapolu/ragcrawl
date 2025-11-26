"""Output/publishing configuration for Markdown export."""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class OutputMode(str, Enum):
    """Markdown output mode."""

    SINGLE = "single"  # Single concatenated Markdown file
    MULTI = "multi"  # One Markdown file per page, preserving folder structure


class DeletionHandling(str, Enum):
    """How to handle deleted pages in multi-page mode."""

    TOMBSTONE = "tombstone"  # Create a tombstone page with deletion notice
    REDIRECT = "redirect"  # Create a redirect stub
    REMOVE = "remove"  # Delete the file


class OutputConfig(BaseModel):
    """
    Configuration for Markdown output/publishing.

    Supports single-page (concatenated) and multi-page (folder structure) modes.
    """

    # Output mode
    mode: OutputMode = Field(
        default=OutputMode.MULTI,
        description="Output mode: single (one file) or multi (per-page files)",
    )

    # Output location
    root_dir: str | Path = Field(
        default="./output",
        description="Root directory for output files",
    )
    single_file_name: str = Field(
        default="site.md",
        description="Filename for single-page mode output",
    )

    # Link handling (multi-page mode)
    rewrite_internal_links: bool = Field(
        default=True,
        description="Rewrite internal links to point to local Markdown files",
    )
    link_extension: str = Field(
        default=".md",
        description="Extension to use for rewritten links",
    )

    # Navigation aids (multi-page mode)
    generate_index: bool = Field(
        default=True,
        description="Generate index/TOC page",
    )
    generate_breadcrumbs: bool = Field(
        default=True,
        description="Add breadcrumb headers to pages",
    )
    generate_prev_next: bool = Field(
        default=False,
        description="Add previous/next navigation links",
    )

    # Single-page mode options
    generate_toc: bool = Field(
        default=True,
        description="Generate table of contents (single-page mode)",
    )
    toc_max_depth: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Maximum heading depth for TOC",
    )
    page_separator: str = Field(
        default="\n\n---\n\n",
        description="Separator between pages in single-page mode",
    )

    # Deletion handling (multi-page mode)
    deletion_handling: DeletionHandling = Field(
        default=DeletionHandling.TOMBSTONE,
        description="How to handle deleted pages",
    )

    # File naming
    strip_extensions: list[str] = Field(
        default_factory=lambda: [".html", ".htm", ".php", ".asp", ".aspx"],
        description="Extensions to strip from output paths",
    )
    index_file_name: str = Field(
        default="index.md",
        description="Name for index files",
    )

    # Content options
    include_metadata_header: bool = Field(
        default=True,
        description="Include YAML frontmatter with metadata",
    )
    include_source_url: bool = Field(
        default=True,
        description="Include source URL in output",
    )

    model_config = {"frozen": False}

    @property
    def output_path(self) -> Path:
        """Get the output root path."""
        return Path(self.root_dir)

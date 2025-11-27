"""Markdown generation configuration for Crawl4AI extraction."""

from enum import Enum

from pydantic import BaseModel, Field


class ContentFilterType(str, Enum):
    """Content filter type for markdown generation."""

    NONE = "none"  # No filtering, use raw markdown
    PRUNING = "pruning"  # PruningContentFilter - removes boilerplate, sidebars, etc.
    BM25 = "bm25"  # BM25ContentFilter - query-focused filtering


class MarkdownConfig(BaseModel):
    """
    Configuration for markdown generation and content filtering.

    Controls how Crawl4AI extracts and filters content for LLM-ready output.
    """

    # === Content Filter ===
    content_filter: ContentFilterType = Field(
        default=ContentFilterType.PRUNING,
        description="Content filter type: none, pruning, or bm25",
    )

    # === PruningContentFilter options ===
    pruning_threshold: float = Field(
        default=0.55,
        ge=0,
        le=1,
        description="Pruning threshold (0-1). Higher = more aggressive filtering",
    )
    pruning_threshold_type: str = Field(
        default="fixed",
        description="Threshold type: 'fixed' or 'dynamic'",
    )
    pruning_min_word_threshold: int = Field(
        default=15,
        ge=0,
        description="Minimum words per content block to keep",
    )

    # === BM25ContentFilter options (requires user_query) ===
    bm25_threshold: float = Field(
        default=1.0,
        ge=0,
        description="BM25 relevance threshold. Higher = stricter matching",
    )
    user_query: str | None = Field(
        default=None,
        description="Query for BM25 filtering (required when content_filter=bm25)",
    )

    # === HTML Content Filtering ===
    excluded_tags: list[str] = Field(
        default_factory=lambda: ["nav", "footer", "header", "aside", "noscript"],
        description="HTML tags to exclude from extraction",
    )
    excluded_selector: str | None = Field(
        default=None,
        description="CSS selector to exclude (e.g., '.sidebar, .ads')",
    )
    css_selector: str | None = Field(
        default=None,
        description="CSS selector to target specific content (e.g., 'article, main, .content')",
    )
    target_elements: list[str] | None = Field(
        default=None,
        description="Target elements for markdown generation (more flexible than css_selector)",
    )

    # === Content Filtering ===
    word_count_threshold: int = Field(
        default=15,
        ge=0,
        description="Minimum words per text block to include",
    )
    remove_overlay_elements: bool = Field(
        default=True,
        description="Remove popups, modals, and overlay elements",
    )
    process_iframes: bool = Field(
        default=True,
        description="Include iframe content in extraction",
    )
    remove_forms: bool = Field(
        default=True,
        description="Remove form elements from output",
    )

    # === Link Filtering ===
    exclude_external_links: bool = Field(
        default=False,
        description="Remove external links from markdown",
    )
    exclude_social_media_links: bool = Field(
        default=True,
        description="Remove social media links (Facebook, Twitter, etc.)",
    )
    exclude_external_images: bool = Field(
        default=False,
        description="Remove images not hosted on the same domain",
    )
    exclude_domains: list[str] = Field(
        default_factory=list,
        description="Specific domains to exclude from links",
    )

    # === Markdown Generator Options ===
    ignore_links: bool = Field(
        default=False,
        description="Remove all hyperlinks from markdown output",
    )
    ignore_images: bool = Field(
        default=False,
        description="Remove all images from markdown output",
    )
    escape_html: bool = Field(
        default=True,
        description="Convert HTML entities to text",
    )
    body_width: int = Field(
        default=0,
        ge=0,
        description="Wrap text at character width (0 = no wrapping)",
    )
    skip_internal_links: bool = Field(
        default=False,
        description="Remove same-page anchor links",
    )
    include_sup_sub: bool = Field(
        default=True,
        description="Handle superscript/subscript formatting",
    )

    # === Output Selection ===
    use_fit_markdown: bool = Field(
        default=True,
        description="Use filtered fit_markdown when available, otherwise raw_markdown",
    )
    include_citations: bool = Field(
        default=False,
        description="Use markdown_with_citations format (reference-style links)",
    )

    model_config = {"frozen": False, "extra": "forbid"}

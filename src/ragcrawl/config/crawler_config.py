"""Main crawler configuration."""

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from ragcrawl.config.output_config import OutputConfig
from ragcrawl.config.storage_config import StorageConfig


class FetchMode(str, Enum):
    """Fetching mode for pages."""

    HTTP = "http"  # HTTP-only (fast)
    BROWSER = "browser"  # Browser rendering (for JS sites)
    HYBRID = "hybrid"  # Try HTTP first, fallback to browser if needed


class RobotsMode(str, Enum):
    """Robots.txt compliance mode."""

    STRICT = "strict"  # Always respect robots.txt
    OFF = "off"  # Ignore robots.txt
    ALLOWLIST = "allowlist"  # Respect for domains not in allowlist


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""

    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    initial_delay: float = Field(default=1.0, ge=0, description="Initial delay in seconds")
    max_delay: float = Field(default=60.0, ge=0, description="Maximum delay in seconds")
    exponential_base: float = Field(default=2.0, ge=1, description="Exponential backoff base")
    retry_statuses: list[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504],
        description="HTTP status codes to retry",
    )


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""

    requests_per_second: float = Field(
        default=2.0, gt=0, description="Global requests per second limit"
    )
    per_domain_rps: float | None = Field(
        default=1.0, description="Per-domain requests per second"
    )
    per_domain_concurrency: int = Field(
        default=2, ge=1, description="Max concurrent requests per domain"
    )
    delay_between_requests: float = Field(
        default=0.5, ge=0, description="Minimum delay between requests in seconds"
    )


class QualityGateConfig(BaseModel):
    """Configuration for content quality gates."""

    min_text_length: int = Field(
        default=100, ge=0, description="Minimum text length in characters"
    )
    min_word_count: int = Field(default=20, ge=0, description="Minimum word count")
    max_duplicate_ratio: float = Field(
        default=0.9,
        ge=0,
        le=1,
        description="Maximum ratio of duplicate content",
    )
    block_patterns: list[str] = Field(
        default_factory=lambda: [
            r"/tag/",
            r"/tags/",
            r"/search",
            r"/page/\d+",
            r"\?.*page=",
        ],
        description="URL patterns to block (thin/low-value pages)",
    )
    detect_language: bool = Field(
        default=False, description="Enable language detection"
    )
    allowed_languages: list[str] | None = Field(
        default=None, description="Allowed languages (None = all)"
    )


class CrawlerConfig(BaseModel):
    """
    Main configuration for the ragcrawl.

    This is the primary configuration object that controls all aspects
    of crawling behavior.
    """

    # === Seed URLs ===
    seeds: list[str] = Field(
        description="Seed URLs to start crawling from",
        min_length=1,
    )

    # === Site identification ===
    site_id: str | None = Field(
        default=None,
        description="Unique site identifier (auto-generated if not provided)",
    )
    site_name: str | None = Field(
        default=None, description="Human-readable site name"
    )

    # === URL Filtering ===
    include_patterns: list[str] = Field(
        default_factory=list,
        description="Regex/glob patterns for URLs to include",
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Regex/glob patterns for URLs to exclude",
    )

    # === Domain constraints ===
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="Allowed domains (empty = seed domains only)",
    )
    allow_subdomains: bool = Field(
        default=True, description="Allow subdomains of allowed_domains"
    )
    allowed_schemes: list[str] = Field(
        default_factory=lambda: ["http", "https"],
        description="Allowed URL schemes",
    )
    allowed_path_prefixes: list[str] = Field(
        default_factory=list,
        description="Allowed path prefixes (empty = all paths)",
    )

    # === Extension/query param filtering ===
    blocked_extensions: list[str] = Field(
        default_factory=lambda: [
            ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z",
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
            ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".exe", ".dmg", ".pkg", ".deb", ".rpm",
        ],
        description="File extensions to skip",
    )
    blocked_query_params: list[str] = Field(
        default_factory=lambda: ["utm_source", "utm_medium", "utm_campaign"],
        description="Query parameters to strip",
    )

    # === Crawl limits ===
    max_depth: int = Field(default=10, ge=0, description="Maximum crawl depth")
    max_pages: int = Field(default=1000, ge=1, description="Maximum pages to crawl")
    max_concurrency: int = Field(
        default=10, ge=1, description="Global max concurrent requests"
    )

    # === Politeness ===
    robots_mode: RobotsMode = Field(
        default=RobotsMode.STRICT, description="Robots.txt compliance mode"
    )
    robots_allowlist: list[str] = Field(
        default_factory=list,
        description="Domains to ignore robots.txt for (when mode=allowlist)",
    )
    user_agent: str = Field(
        default="ragcrawl/0.1 (+https://github.com/datalync/ragcrawl)",
        description="User-Agent string",
    )
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description="Rate limiting configuration"
    )
    retry: RetryConfig = Field(
        default_factory=RetryConfig, description="Retry configuration"
    )

    # === Fetching ===
    fetch_mode: FetchMode = Field(
        default=FetchMode.HTTP, description="Fetching mode"
    )
    render_js: bool = Field(
        default=False, description="Enable JavaScript rendering"
    )
    browser_timeout: int = Field(
        default=30000, ge=1000, description="Browser timeout in ms"
    )
    http_timeout: int = Field(
        default=30, ge=1, description="HTTP request timeout in seconds"
    )

    # === HTTP options ===
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")
    max_redirects: int = Field(default=10, ge=0, description="Maximum redirects to follow")
    cookies: dict[str, str] = Field(
        default_factory=dict, description="Cookies to send with requests"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Additional HTTP headers"
    )
    proxy: str | None = Field(default=None, description="Proxy URL")

    # === Content options ===
    extract_html: bool = Field(
        default=False, description="Also store cleaned HTML"
    )
    extract_plain_text: bool = Field(
        default=False, description="Also store plain text"
    )
    quality_gates: QualityGateConfig = Field(
        default_factory=QualityGateConfig, description="Quality gate configuration"
    )

    # === Storage ===
    storage: StorageConfig = Field(
        default_factory=StorageConfig, description="Storage backend configuration"
    )

    # === Output ===
    output: OutputConfig = Field(
        default_factory=OutputConfig, description="Output/publishing configuration"
    )

    # === Hooks (not serializable) ===
    on_page: Callable[..., Any] | None = Field(
        default=None, description="Callback on each page crawled", exclude=True
    )
    on_error: Callable[..., Any] | None = Field(
        default=None, description="Callback on errors", exclude=True
    )
    on_change_detected: Callable[..., Any] | None = Field(
        default=None, description="Callback when content changes", exclude=True
    )
    redaction_hook: Callable[[str], str] | None = Field(
        default=None, description="Hook to redact sensitive content", exclude=True
    )

    model_config = {"frozen": False, "extra": "allow"}

    def get_allowed_domains(self) -> set[str]:
        """Get the set of allowed domains including seed domains."""
        from urllib.parse import urlparse

        domains = set(self.allowed_domains)
        for seed in self.seeds:
            parsed = urlparse(seed)
            if parsed.netloc:
                domains.add(parsed.netloc)
        return domains

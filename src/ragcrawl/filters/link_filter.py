"""Link filtering based on domain, path, and pattern constraints."""

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

import tldextract

from ragcrawl.filters.patterns import ExtensionFilter, PatternMatcher
from ragcrawl.filters.url_normalizer import URLNormalizer


class FilterReason(str, Enum):
    """Reason for filtering a URL."""

    ALLOWED = "allowed"
    INVALID_URL = "invalid_url"
    INVALID_SCHEME = "invalid_scheme"
    DOMAIN_NOT_ALLOWED = "domain_not_allowed"
    PATH_NOT_ALLOWED = "path_not_allowed"
    BLOCKED_EXTENSION = "blocked_extension"
    EXCLUDED_PATTERN = "excluded_pattern"
    NO_INCLUDE_MATCH = "no_include_match"
    ALREADY_SEEN = "already_seen"
    MAX_DEPTH_EXCEEDED = "max_depth_exceeded"
    ROBOTS_BLOCKED = "robots_blocked"


@dataclass
class FilterResult:
    """Result of URL filtering."""

    allowed: bool
    reason: FilterReason
    normalized_url: str | None = None
    details: str | None = None


class LinkFilter:
    """
    Filters URLs based on domain, path, extension, and pattern constraints.

    This is the main filter used by the crawler to determine which URLs
    to include in the frontier.
    """

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        allow_subdomains: bool = True,
        allowed_schemes: list[str] | None = None,
        allowed_path_prefixes: list[str] | None = None,
        blocked_extensions: list[str] | None = None,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        blocked_query_params: list[str] | None = None,
    ) -> None:
        """
        Initialize the link filter.

        Args:
            allowed_domains: Domains to allow (empty = all).
            allow_subdomains: Whether to allow subdomains of allowed_domains.
            allowed_schemes: URL schemes to allow (default: http, https).
            allowed_path_prefixes: Path prefixes to allow (empty = all).
            blocked_extensions: File extensions to block.
            include_patterns: Regex/glob patterns for URLs to include.
            exclude_patterns: Regex/glob patterns for URLs to exclude.
            blocked_query_params: Query parameters to strip.
        """
        self.allowed_domains = set(d.lower() for d in (allowed_domains or []))
        self.allow_subdomains = allow_subdomains
        self.allowed_schemes = set(s.lower() for s in (allowed_schemes or ["http", "https"]))
        self.allowed_path_prefixes = list(allowed_path_prefixes or [])

        self.normalizer = URLNormalizer(remove_query_params=blocked_query_params)
        self.pattern_matcher = PatternMatcher(include_patterns, exclude_patterns)
        self.extension_filter = ExtensionFilter(blocked_extensions)

        # Track seen URLs for deduplication
        self._seen_urls: set[str] = set()

    def filter(
        self,
        url: str,
        check_seen: bool = True,
        current_depth: int = 0,
        max_depth: int | None = None,
    ) -> FilterResult:
        """
        Filter a URL and return the result.

        Args:
            url: The URL to filter.
            check_seen: Whether to check if URL was already seen.
            current_depth: Current crawl depth.
            max_depth: Maximum allowed depth.

        Returns:
            FilterResult with allowed status and reason.
        """
        # Parse and validate URL
        try:
            parsed = urlparse(url)
        except Exception:
            return FilterResult(
                allowed=False,
                reason=FilterReason.INVALID_URL,
                details="Failed to parse URL",
            )

        if not parsed.scheme or not parsed.netloc:
            return FilterResult(
                allowed=False,
                reason=FilterReason.INVALID_URL,
                details="Missing scheme or netloc",
            )

        # Scheme check
        if parsed.scheme.lower() not in self.allowed_schemes:
            return FilterResult(
                allowed=False,
                reason=FilterReason.INVALID_SCHEME,
                details=f"Scheme '{parsed.scheme}' not allowed",
            )

        # Normalize URL
        normalized = self.normalizer.normalize(url)

        # Deduplication check
        if check_seen and normalized in self._seen_urls:
            return FilterResult(
                allowed=False,
                reason=FilterReason.ALREADY_SEEN,
                normalized_url=normalized,
            )

        # Depth check
        if max_depth is not None and current_depth > max_depth:
            return FilterResult(
                allowed=False,
                reason=FilterReason.MAX_DEPTH_EXCEEDED,
                normalized_url=normalized,
                details=f"Depth {current_depth} exceeds max {max_depth}",
            )

        # Domain check
        if self.allowed_domains:
            hostname = parsed.netloc.lower()
            # Remove port if present
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            if not self._is_domain_allowed(hostname):
                return FilterResult(
                    allowed=False,
                    reason=FilterReason.DOMAIN_NOT_ALLOWED,
                    normalized_url=normalized,
                    details=f"Domain '{hostname}' not in allowed list",
                )

        # Path prefix check
        if self.allowed_path_prefixes:
            path = parsed.path
            if not any(path.startswith(prefix) for prefix in self.allowed_path_prefixes):
                return FilterResult(
                    allowed=False,
                    reason=FilterReason.PATH_NOT_ALLOWED,
                    normalized_url=normalized,
                    details=f"Path '{path}' doesn't match allowed prefixes",
                )

        # Extension check
        if self.extension_filter.is_blocked(url):
            ext = self.extension_filter.get_extension(url)
            return FilterResult(
                allowed=False,
                reason=FilterReason.BLOCKED_EXTENSION,
                normalized_url=normalized,
                details=f"Extension '{ext}' is blocked",
            )

        # Pattern check
        if not self.pattern_matcher.should_include(url):
            reason = self.pattern_matcher.get_match_reason(url)
            if self.pattern_matcher.matches_exclude(url):
                return FilterResult(
                    allowed=False,
                    reason=FilterReason.EXCLUDED_PATTERN,
                    normalized_url=normalized,
                    details=reason,
                )
            else:
                return FilterResult(
                    allowed=False,
                    reason=FilterReason.NO_INCLUDE_MATCH,
                    normalized_url=normalized,
                    details=reason,
                )

        # URL is allowed
        return FilterResult(
            allowed=True,
            reason=FilterReason.ALLOWED,
            normalized_url=normalized,
        )

    def _is_domain_allowed(self, hostname: str) -> bool:
        """
        Check if hostname is in allowed domains.

        Args:
            hostname: The hostname to check.

        Returns:
            True if allowed.
        """
        # Direct match
        if hostname in self.allowed_domains:
            return True

        # Subdomain match
        if self.allow_subdomains:
            extracted = tldextract.extract(hostname)
            registered_domain = f"{extracted.domain}.{extracted.suffix}".lower()

            if registered_domain in self.allowed_domains:
                return True

            # Check if any allowed domain is a parent of this hostname
            for allowed in self.allowed_domains:
                if hostname.endswith(f".{allowed}"):
                    return True

        return False

    def mark_seen(self, url: str) -> str:
        """
        Mark a URL as seen and return normalized form.

        Args:
            url: The URL to mark.

        Returns:
            The normalized URL.
        """
        normalized = self.normalizer.normalize(url)
        self._seen_urls.add(normalized)
        return normalized

    def is_seen(self, url: str) -> bool:
        """
        Check if URL has been seen.

        Args:
            url: The URL to check.

        Returns:
            True if URL has been seen.
        """
        normalized = self.normalizer.normalize(url)
        return normalized in self._seen_urls

    def clear_seen(self) -> None:
        """Clear the set of seen URLs."""
        self._seen_urls.clear()

    @property
    def seen_count(self) -> int:
        """Get the count of seen URLs."""
        return len(self._seen_urls)

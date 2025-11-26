"""Link extraction from HTML content."""

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse


@dataclass
class ExtractedLink:
    """An extracted link with metadata."""

    href: str
    text: str | None = None
    is_internal: bool = False
    is_nofollow: bool = False
    anchor: str | None = None  # Fragment identifier


class LinkExtractor:
    """
    Extracts and categorizes links from HTML content.
    """

    def __init__(
        self,
        base_url: str,
        allowed_domains: set[str] | None = None,
    ) -> None:
        """
        Initialize link extractor.

        Args:
            base_url: Base URL for resolving relative links.
            allowed_domains: Domains to consider as internal.
        """
        self.base_url = base_url
        self.base_parsed = urlparse(base_url)
        self.base_domain = self.base_parsed.netloc.lower()

        self.allowed_domains = allowed_domains or {self.base_domain}

    def extract(self, html: str) -> list[ExtractedLink]:
        """
        Extract all links from HTML.

        Args:
            html: HTML content.

        Returns:
            List of extracted links.
        """
        links: list[ExtractedLink] = []
        seen_hrefs: set[str] = set()

        # Match anchor tags
        pattern = r"<a\s+([^>]*)>(.*?)</a>"
        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            attrs = match.group(1)
            text = self._clean_text(match.group(2))

            # Extract href
            href_match = re.search(r'href=["\']([^"\']+)["\']', attrs)
            if not href_match:
                continue

            href = href_match.group(1).strip()

            # Skip javascript:, mailto:, tel:, etc.
            if self._is_special_scheme(href):
                continue

            # Resolve relative URLs
            resolved = self._resolve_url(href)
            if not resolved:
                continue

            # Deduplicate
            normalized = self._normalize_for_dedup(resolved)
            if normalized in seen_hrefs:
                continue
            seen_hrefs.add(normalized)

            # Check if nofollow
            is_nofollow = "nofollow" in attrs.lower()

            # Check if internal
            is_internal = self._is_internal(resolved)

            # Extract anchor
            anchor = None
            parsed = urlparse(resolved)
            if parsed.fragment:
                anchor = parsed.fragment

            links.append(
                ExtractedLink(
                    href=resolved,
                    text=text if text else None,
                    is_internal=is_internal,
                    is_nofollow=is_nofollow,
                    anchor=anchor,
                )
            )

        return links

    def extract_urls(self, html: str) -> list[str]:
        """
        Extract just the URLs from HTML.

        Args:
            html: HTML content.

        Returns:
            List of resolved URLs.
        """
        return [link.href for link in self.extract(html)]

    def extract_internal_urls(self, html: str) -> list[str]:
        """
        Extract only internal URLs.

        Args:
            html: HTML content.

        Returns:
            List of internal URLs.
        """
        return [link.href for link in self.extract(html) if link.is_internal]

    def extract_external_urls(self, html: str) -> list[str]:
        """
        Extract only external URLs.

        Args:
            html: HTML content.

        Returns:
            List of external URLs.
        """
        return [link.href for link in self.extract(html) if not link.is_internal]

    def _resolve_url(self, href: str) -> str | None:
        """Resolve a URL relative to base URL."""
        try:
            resolved = urljoin(self.base_url, href)
            parsed = urlparse(resolved)

            # Only allow http/https
            if parsed.scheme not in ("http", "https"):
                return None

            return resolved

        except Exception:
            return None

    def _is_internal(self, url: str) -> bool:
        """Check if URL is internal."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Direct domain match
            if domain in self.allowed_domains:
                return True

            # Check subdomains
            for allowed in self.allowed_domains:
                if domain.endswith(f".{allowed}"):
                    return True

            return False

        except Exception:
            return False

    def _is_special_scheme(self, href: str) -> bool:
        """Check if href has a special scheme to skip."""
        special = (
            "javascript:",
            "mailto:",
            "tel:",
            "data:",
            "#",
            "void(",
        )
        return any(href.lower().startswith(s) for s in special)

    def _normalize_for_dedup(self, url: str) -> str:
        """Normalize URL for deduplication."""
        try:
            parsed = urlparse(url)
            # Remove fragment for dedup
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return url

    def _clean_text(self, text: str) -> str:
        """Clean link text."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

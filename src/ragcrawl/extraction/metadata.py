"""Metadata extraction from HTML pages."""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HeadingInfo:
    """Information about a heading."""

    level: int
    text: str
    anchor: str | None = None


@dataclass
class PageMetadata:
    """Extracted metadata from a page."""

    title: str | None = None
    description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    author: str | None = None
    published_date: str | None = None
    modified_date: str | None = None
    keywords: list[str] = field(default_factory=list)
    headings_outline: list[HeadingInfo] = field(default_factory=list)
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_type: str | None = None
    word_count: int = 0
    char_count: int = 0


class MetadataExtractor:
    """
    Extracts metadata from HTML pages.
    """

    def extract(self, html: str, text: str | None = None) -> PageMetadata:
        """
        Extract metadata from HTML.

        Args:
            html: HTML content.
            text: Optional plain text for word/char counting.

        Returns:
            PageMetadata with extracted values.
        """
        metadata = PageMetadata()

        # Title
        metadata.title = self._extract_title(html)

        # Meta tags
        metadata.description = self._extract_meta(html, "description")
        metadata.keywords = self._extract_keywords(html)
        metadata.author = self._extract_meta(html, "author")
        metadata.canonical_url = self._extract_canonical(html)
        metadata.language = self._extract_language(html)

        # Dates
        metadata.published_date = self._extract_meta(
            html, "article:published_time"
        ) or self._extract_meta(html, "datePublished")
        metadata.modified_date = self._extract_meta(
            html, "article:modified_time"
        ) or self._extract_meta(html, "dateModified")

        # Open Graph
        metadata.og_title = self._extract_meta(html, "og:title", property_attr=True)
        metadata.og_description = self._extract_meta(html, "og:description", property_attr=True)
        metadata.og_image = self._extract_meta(html, "og:image", property_attr=True)
        metadata.og_type = self._extract_meta(html, "og:type", property_attr=True)

        # Headings outline
        metadata.headings_outline = self._extract_headings(html)

        # Word/char count
        if text:
            metadata.word_count = len(text.split())
            metadata.char_count = len(text)

        return metadata

    def _extract_title(self, html: str) -> str | None:
        """Extract page title."""
        # Try <title> tag first
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))

        # Try og:title
        og_title = self._extract_meta(html, "og:title", property_attr=True)
        if og_title:
            return og_title

        # Try first h1
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))

        return None

    def _extract_meta(
        self, html: str, name: str, property_attr: bool = False
    ) -> str | None:
        """Extract meta tag content."""
        attr = "property" if property_attr else "name"

        patterns = [
            rf'<meta[^>]+{attr}=["\']?{re.escape(name)}["\']?[^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+{attr}=["\']?{re.escape(name)}["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))

        return None

    def _extract_canonical(self, html: str) -> str | None:
        """Extract canonical URL."""
        match = re.search(
            r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)

        match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)

        return None

    def _extract_language(self, html: str) -> str | None:
        """Extract page language."""
        # Try html lang attribute
        match = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1).split("-")[0].lower()

        # Try meta Content-Language
        return self._extract_meta(html, "Content-Language")

    def _extract_keywords(self, html: str) -> list[str]:
        """Extract keywords."""
        keywords_str = self._extract_meta(html, "keywords")
        if keywords_str:
            return [k.strip() for k in keywords_str.split(",") if k.strip()]
        return []

    def _extract_headings(self, html: str) -> list[HeadingInfo]:
        """Extract headings outline."""
        headings = []

        pattern = r"<(h[1-6])([^>]*)>([^<]*)</h[1-6]>"
        for match in re.finditer(pattern, html, re.IGNORECASE):
            tag = match.group(1).lower()
            attrs = match.group(2)
            text = self._clean_text(match.group(3))

            if not text:
                continue

            level = int(tag[1])

            # Try to extract id/anchor
            anchor = None
            id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
            if id_match:
                anchor = id_match.group(1)

            headings.append(HeadingInfo(level=level, text=text, anchor=anchor))

        return headings

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Decode HTML entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

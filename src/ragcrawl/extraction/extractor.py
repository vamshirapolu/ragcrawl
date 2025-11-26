"""Content extraction from fetched pages."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from ragcrawl.extraction.link_extractor import LinkExtractor
from ragcrawl.extraction.metadata import MetadataExtractor, PageMetadata
from ragcrawl.fetcher.base import FetchResult
from ragcrawl.utils.hashing import compute_content_hash


@dataclass
class ExtractionResult:
    """Result of content extraction."""

    # Content
    markdown: str
    html: str | None = None
    plain_text: str | None = None

    # Hashes
    content_hash: str = ""
    raw_hash: str | None = None

    # Metadata
    metadata: PageMetadata = field(default_factory=PageMetadata)

    # Links
    outlinks: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)

    # Timing
    extraction_latency_ms: float = 0.0

    # Status
    success: bool = True
    error: str | None = None


class ExtractorProtocol(Protocol):
    """Protocol for content extractors."""

    def extract(
        self,
        fetch_result: FetchResult,
        url: str,
        extract_html: bool = False,
        extract_plain_text: bool = False,
    ) -> ExtractionResult:
        """Extract content from a fetch result."""
        ...


class ContentExtractor:
    """
    Extracts structured content from fetched pages.

    Combines markdown extraction, metadata, and link extraction.
    """

    def __init__(
        self,
        allowed_domains: set[str] | None = None,
    ) -> None:
        """
        Initialize content extractor.

        Args:
            allowed_domains: Domains to consider as internal.
        """
        self.allowed_domains = allowed_domains or set()
        self.metadata_extractor = MetadataExtractor()

    def extract(
        self,
        fetch_result: FetchResult,
        url: str,
        extract_html: bool = False,
        extract_plain_text: bool = False,
    ) -> ExtractionResult:
        """
        Extract content from a fetch result.

        Args:
            fetch_result: Result from fetcher.
            url: URL of the page.
            extract_html: Whether to include cleaned HTML.
            extract_plain_text: Whether to include plain text.

        Returns:
            ExtractionResult with extracted content.
        """
        import time

        start_time = time.time()

        try:
            # Get markdown (already extracted by fetcher or fallback)
            markdown = fetch_result.markdown or ""

            # Compute content hash
            content_hash = compute_content_hash(markdown)

            # Get HTML
            html = fetch_result.html
            raw_hash = compute_content_hash(html) if html else None

            # Extract metadata
            if html:
                metadata = self.metadata_extractor.extract(html, markdown)
            else:
                metadata = PageMetadata(
                    title=fetch_result.title,
                    description=fetch_result.description,
                    word_count=len(markdown.split()),
                    char_count=len(markdown),
                )

            # Override with fetch result if available
            if fetch_result.title:
                metadata.title = fetch_result.title
            if fetch_result.description:
                metadata.description = fetch_result.description

            # Extract links
            link_extractor = LinkExtractor(
                base_url=url,
                allowed_domains=self.allowed_domains,
            )

            if html:
                links = link_extractor.extract(html)
                outlinks = [link.href for link in links]
                internal_links = [link.href for link in links if link.is_internal]
                external_links = [link.href for link in links if not link.is_internal]
            else:
                # Use links from fetch result
                outlinks = fetch_result.links or []
                internal_links = [
                    link for link in outlinks if self._is_internal(link, url)
                ]
                external_links = [
                    link for link in outlinks if not self._is_internal(link, url)
                ]

            # Generate plain text if requested
            plain_text = None
            if extract_plain_text:
                plain_text = self._markdown_to_text(markdown)

            latency_ms = (time.time() - start_time) * 1000

            return ExtractionResult(
                markdown=markdown,
                html=html if extract_html else None,
                plain_text=plain_text,
                content_hash=content_hash,
                raw_hash=raw_hash,
                metadata=metadata,
                outlinks=outlinks,
                internal_links=internal_links,
                external_links=external_links,
                extraction_latency_ms=latency_ms,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ExtractionResult(
                markdown="",
                extraction_latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

    def _is_internal(self, link: str, base_url: str) -> bool:
        """Check if link is internal."""
        from urllib.parse import urlparse

        try:
            link_parsed = urlparse(link)
            base_parsed = urlparse(base_url)

            link_domain = link_parsed.netloc.lower()
            base_domain = base_parsed.netloc.lower()

            if link_domain == base_domain:
                return True

            if link_domain in self.allowed_domains:
                return True

            for domain in self.allowed_domains:
                if link_domain.endswith(f".{domain}"):
                    return True

            return False

        except Exception:
            return False

    def _markdown_to_text(self, markdown: str) -> str:
        """Convert markdown to plain text."""
        import re

        text = markdown

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"`[^`]+`", "", text)

        # Remove images
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)

        # Convert links to just text
        text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

        # Remove headers markers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove bold/italic
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Remove horizontal rules
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)

        # Remove list markers
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)

        return text.strip()

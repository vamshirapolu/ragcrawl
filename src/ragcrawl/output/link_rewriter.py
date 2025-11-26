"""Internal link rewriting for multi-page output."""

import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from ragcrawl.config.output_config import OutputConfig


class LinkRewriter:
    """
    Rewrites internal links to point to local markdown files.
    """

    def __init__(self, config: OutputConfig) -> None:
        """
        Initialize link rewriter.

        Args:
            config: Output configuration.
        """
        self.config = config
        self._url_to_path: dict[str, Path] = {}

        # Regex for markdown links
        self._link_pattern = re.compile(
            r"\[([^\]]+)\]\(([^)]+)\)",
            re.MULTILINE,
        )

    def set_url_mapping(self, mapping: dict[str, Path]) -> None:
        """
        Set the URL to path mapping.

        Args:
            mapping: Dict mapping URLs to output paths.
        """
        self._url_to_path = mapping

    def rewrite(self, content: str, source_url: str) -> str:
        """
        Rewrite links in content.

        Args:
            content: Markdown content.
            source_url: URL of the source page.

        Returns:
            Content with rewritten links.
        """
        if not self.config.rewrite_internal_links:
            return content

        def replace_link(match: re.Match) -> str:
            text = match.group(1)
            href = match.group(2)

            # Skip non-http links
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                return match.group(0)

            # Resolve relative URLs
            if not href.startswith(("http://", "https://")):
                href = urljoin(source_url, href)

            # Check if it's an internal link we know about
            # Normalize the URL
            parsed = urlparse(href)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            if normalized in self._url_to_path:
                local_path = self._url_to_path[normalized]
                # Calculate relative path from source
                source_path = self._url_to_path.get(source_url)
                if source_path:
                    relative = self._get_relative_path(source_path, local_path)
                    return f"[{text}]({relative})"

            # Keep original link for external URLs
            return match.group(0)

        return self._link_pattern.sub(replace_link, content)

    def _get_relative_path(self, from_path: Path, to_path: Path) -> str:
        """Calculate relative path between two files."""
        # Get directories
        from_dir = from_path.parent
        to_dir = to_path.parent

        # Find common ancestor
        from_parts = list(from_dir.parts)
        to_parts = list(to_dir.parts)

        common_length = 0
        for i, (a, b) in enumerate(zip(from_parts, to_parts)):
            if a != b:
                break
            common_length = i + 1

        # Build relative path
        ups = len(from_parts) - common_length
        rel_parts = [".."] * ups + list(to_parts[common_length:]) + [to_path.name]

        return "/".join(rel_parts) if rel_parts else to_path.name

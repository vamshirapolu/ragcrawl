"""Single-page markdown publisher."""

from pathlib import Path
from urllib.parse import urlparse

from ragcrawl.config.output_config import OutputConfig
from ragcrawl.models.document import Document
from ragcrawl.output.publisher import MarkdownPublisher


class SinglePagePublisher(MarkdownPublisher):
    """
    Publishes all documents to a single markdown file.

    Features:
    - Auto-generated table of contents
    - Per-page anchors for navigation
    - Configurable page separators
    """

    def publish(self, documents: list[Document]) -> list[Path]:
        """
        Publish all documents to a single file.

        Args:
            documents: Documents to publish.

        Returns:
            List containing the single output file path.
        """
        if not documents:
            return []

        self.ensure_output_dir()

        # Sort documents by depth, then URL
        sorted_docs = sorted(documents, key=lambda d: (d.depth, d.normalized_url))

        # Build content
        content_parts = []

        # Generate TOC if enabled
        if self.config.generate_toc:
            toc = self._generate_toc(sorted_docs)
            content_parts.append(toc)
            content_parts.append(self.config.page_separator)

        # Add each document
        for doc in sorted_docs:
            page_content = self._format_document(doc)
            content_parts.append(page_content)
            content_parts.append(self.config.page_separator)

        # Write file
        output_file = self.output_path / self.config.single_file_name
        output_file.write_text("".join(content_parts))

        return [output_file]

    def publish_single(self, document: Document) -> Path | None:
        """Single page mode doesn't support individual publishing."""
        return None

    def _generate_toc(self, documents: list[Document]) -> str:
        """Generate table of contents."""
        lines = ["# Table of Contents\n"]

        for doc in documents:
            # Create anchor from URL
            anchor = self._url_to_anchor(doc.normalized_url)
            title = doc.title or self._url_to_title(doc.normalized_url)

            # Indent based on depth (max 3 levels)
            indent = "  " * min(doc.depth, self.config.toc_max_depth - 1)
            lines.append(f"{indent}- [{title}](#{anchor})")

        return "\n".join(lines)

    def _format_document(self, document: Document) -> str:
        """Format a document for inclusion in the single file."""
        parts = []

        # Anchor for navigation
        anchor = self._url_to_anchor(document.normalized_url)
        parts.append(f'<a id="{anchor}"></a>\n')

        # Metadata header
        if self.config.include_metadata_header:
            parts.append(self._format_frontmatter(document))

        # Source URL
        if self.config.include_source_url:
            parts.append(f"*Source: [{document.normalized_url}]({document.normalized_url})*\n\n")

        # Content
        parts.append(document.markdown)

        return "\n".join(parts)

    def _format_frontmatter(self, document: Document) -> str:
        """Format YAML frontmatter."""
        title = document.title or self._url_to_title(document.normalized_url)
        return f"## {title}\n\n"

    def _url_to_anchor(self, url: str) -> str:
        """Convert URL to valid anchor ID."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        # Replace special characters
        anchor = path.replace("/", "-").replace(".", "-")
        anchor = "".join(c if c.isalnum() or c == "-" else "" for c in anchor)

        return anchor or "index"

    def _url_to_title(self, url: str) -> str:
        """Convert URL to readable title."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return parsed.netloc

        # Get last segment
        segments = path.split("/")
        title = segments[-1]

        # Remove extension
        if "." in title:
            title = title.rsplit(".", 1)[0]

        # Convert to title case
        title = title.replace("-", " ").replace("_", " ").title()

        return title

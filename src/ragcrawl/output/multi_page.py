"""Multi-page markdown publisher."""

from pathlib import Path
from urllib.parse import urlparse

from ragcrawl.config.output_config import DeletionHandling, OutputConfig
from ragcrawl.models.document import Document
from ragcrawl.output.link_rewriter import LinkRewriter
from ragcrawl.output.navigation import NavigationGenerator
from ragcrawl.output.publisher import MarkdownPublisher


class MultiPagePublisher(MarkdownPublisher):
    """
    Publishes documents as individual markdown files.

    Features:
    - Preserves site folder structure
    - Rewrites internal links to local markdown files
    - Generates navigation aids (index, breadcrumbs, prev/next)
    - Handles deleted pages via tombstones or redirects
    """

    def __init__(self, config: OutputConfig) -> None:
        """Initialize multi-page publisher."""
        super().__init__(config)
        self.link_rewriter = LinkRewriter(config)
        self.nav_generator = NavigationGenerator(config)

    def publish(self, documents: list[Document]) -> list[Path]:
        """
        Publish documents as individual files.

        Args:
            documents: Documents to publish.

        Returns:
            List of created file paths.
        """
        if not documents:
            return []

        self.ensure_output_dir()

        # Build URL to path mapping for link rewriting
        url_to_path = {}
        for doc in documents:
            output_path = self._url_to_path(doc.normalized_url)
            url_to_path[doc.normalized_url] = output_path

        self.link_rewriter.set_url_mapping(url_to_path)

        # Sort by depth for proper ordering
        sorted_docs = sorted(documents, key=lambda d: (d.depth, d.normalized_url))

        created_files = []

        # Publish each document
        for i, doc in enumerate(sorted_docs):
            # Get prev/next for navigation
            prev_doc = sorted_docs[i - 1] if i > 0 else None
            next_doc = sorted_docs[i + 1] if i < len(sorted_docs) - 1 else None

            file_path = self._publish_document(doc, prev_doc, next_doc)
            if file_path:
                created_files.append(file_path)

        # Generate index if enabled
        if self.config.generate_index:
            index_path = self._generate_index(sorted_docs)
            created_files.append(index_path)

        return created_files

    def publish_single(self, document: Document) -> Path | None:
        """
        Publish a single document.

        Args:
            document: Document to publish.

        Returns:
            Created file path.
        """
        self.ensure_output_dir()
        return self._publish_document(document, None, None)

    def _publish_document(
        self,
        document: Document,
        prev_doc: Document | None,
        next_doc: Document | None,
    ) -> Path | None:
        """Publish a single document to disk."""
        if document.is_tombstone:
            return self._handle_tombstone(document)

        output_path = self._url_to_path(document.normalized_url)

        # Build content
        content_parts = []

        # Frontmatter
        if self.config.include_metadata_header:
            content_parts.append(self._format_frontmatter(document))

        # Breadcrumbs
        if self.config.generate_breadcrumbs:
            breadcrumbs = self.nav_generator.generate_breadcrumbs(document)
            content_parts.append(breadcrumbs + "\n\n")

        # Source URL
        if self.config.include_source_url:
            content_parts.append(
                f"*Source: [{document.normalized_url}]({document.normalized_url})*\n\n"
            )

        # Main content with rewritten links
        rewritten_content = self.link_rewriter.rewrite(
            document.markdown, document.normalized_url
        )
        content_parts.append(rewritten_content)

        # Prev/next navigation
        if self.config.generate_prev_next and (prev_doc or next_doc):
            nav = self.nav_generator.generate_prev_next(prev_doc, next_doc)
            content_parts.append("\n\n" + nav)

        # Write file
        full_path = self.output_path / output_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("\n".join(content_parts))

        return full_path

    def _handle_tombstone(self, document: Document) -> Path | None:
        """Handle a tombstoned (deleted) document."""
        output_path = self._url_to_path(document.normalized_url)
        full_path = self.output_path / output_path

        if self.config.deletion_handling == DeletionHandling.REMOVE:
            # Delete the file if it exists
            if full_path.exists():
                full_path.unlink()
            return None

        elif self.config.deletion_handling == DeletionHandling.TOMBSTONE:
            # Create tombstone page
            content = f"""---
title: Page Removed
status: deleted
original_url: {document.normalized_url}
---

# Page Removed

This page has been removed from the source site.

*Original URL: {document.normalized_url}*
"""
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return full_path

        elif self.config.deletion_handling == DeletionHandling.REDIRECT:
            # Create redirect stub
            content = f"""---
redirect_to: /
original_url: {document.normalized_url}
---

This page has moved. Please see the [index](/{self.config.index_file_name}).
"""
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            return full_path

        return None

    def _generate_index(self, documents: list[Document]) -> Path:
        """Generate index/TOC page."""
        content = self.nav_generator.generate_index(documents)
        index_path = self.output_path / self.config.index_file_name
        index_path.write_text(content)
        return index_path

    def _url_to_path(self, url: str) -> Path:
        """Convert URL to output file path."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return Path(self.config.index_file_name)

        # Strip configured extensions
        for ext in self.config.strip_extensions:
            if path.endswith(ext):
                path = path[: -len(ext)]
                break

        # Handle directory-style URLs
        if not path.endswith(".md"):
            # Check if it looks like a file or directory
            last_segment = path.split("/")[-1] if "/" in path else path
            if "." not in last_segment:
                # It's a directory-style URL
                path = f"{path}/{self.config.index_file_name}"
            else:
                path = f"{path}{self.config.link_extension}"

        # Ensure .md extension
        if not path.endswith(".md"):
            path = f"{path}.md"

        return Path(path)

    def _format_frontmatter(self, document: Document) -> str:
        """Format YAML frontmatter."""
        title = document.title or "Untitled"
        # Escape quotes in title
        title = title.replace('"', '\\"')

        frontmatter = f"""---
title: "{title}"
url: {document.normalized_url}
"""
        if document.description:
            desc = document.description.replace('"', '\\"')
            frontmatter += f'description: "{desc}"\n'

        if document.last_crawled:
            frontmatter += f"crawled_at: {document.last_crawled.isoformat()}\n"

        frontmatter += "---\n"
        return frontmatter

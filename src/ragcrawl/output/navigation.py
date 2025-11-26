"""Navigation generation for multi-page output."""

from pathlib import Path
from urllib.parse import urlparse

from ragcrawl.config.output_config import OutputConfig
from ragcrawl.models.document import Document


class NavigationGenerator:
    """
    Generates navigation elements for multi-page output.
    """

    def __init__(self, config: OutputConfig) -> None:
        """
        Initialize navigation generator.

        Args:
            config: Output configuration.
        """
        self.config = config

    def generate_breadcrumbs(self, document: Document) -> str:
        """
        Generate breadcrumb navigation.

        Args:
            document: Document to generate breadcrumbs for.

        Returns:
            Markdown breadcrumb string.
        """
        parsed = urlparse(document.normalized_url)
        path_parts = parsed.path.strip("/").split("/")

        if not path_parts or path_parts == [""]:
            return ""

        breadcrumbs = ["[Home](/" + self.config.index_file_name + ")"]

        # Build breadcrumb for each level
        current_path = ""
        for i, part in enumerate(path_parts[:-1]):
            current_path += f"/{part}"
            title = part.replace("-", " ").replace("_", " ").title()
            breadcrumbs.append(f"[{title}]({current_path}/{self.config.index_file_name})")

        # Current page (not a link)
        title = document.title or path_parts[-1].replace("-", " ").replace("_", " ").title()
        breadcrumbs.append(title)

        return " > ".join(breadcrumbs)

    def generate_prev_next(
        self,
        prev_doc: Document | None,
        next_doc: Document | None,
    ) -> str:
        """
        Generate previous/next navigation.

        Args:
            prev_doc: Previous document in sequence.
            next_doc: Next document in sequence.

        Returns:
            Markdown navigation string.
        """
        parts = []

        parts.append("---\n")

        if prev_doc:
            prev_title = prev_doc.title or "Previous"
            prev_path = self._url_to_path(prev_doc.normalized_url)
            parts.append(f"**Previous:** [{prev_title}]({prev_path})")

        if prev_doc and next_doc:
            parts.append(" | ")

        if next_doc:
            next_title = next_doc.title or "Next"
            next_path = self._url_to_path(next_doc.normalized_url)
            parts.append(f"**Next:** [{next_title}]({next_path})")

        return "".join(parts)

    def generate_index(self, documents: list[Document]) -> str:
        """
        Generate index/TOC page.

        Args:
            documents: All documents in the site.

        Returns:
            Markdown index content.
        """
        lines = [
            "---",
            "title: Index",
            "---",
            "",
            "# Documentation Index",
            "",
        ]

        # Group by depth/path
        by_path: dict[str, list[Document]] = {}
        for doc in documents:
            if doc.is_tombstone:
                continue

            parsed = urlparse(doc.normalized_url)
            path = parsed.path.strip("/")
            parts = path.split("/")

            if len(parts) > 1:
                section = parts[0]
            else:
                section = "/"

            if section not in by_path:
                by_path[section] = []
            by_path[section].append(doc)

        # Generate sections
        for section, docs in sorted(by_path.items()):
            if section != "/":
                section_title = section.replace("-", " ").replace("_", " ").title()
                lines.append(f"\n## {section_title}\n")

            for doc in sorted(docs, key=lambda d: d.normalized_url):
                title = doc.title or self._url_to_title(doc.normalized_url)
                path = self._url_to_path(doc.normalized_url)
                lines.append(f"- [{title}]({path})")

        return "\n".join(lines)

    def _url_to_path(self, url: str) -> str:
        """Convert URL to relative output path."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return self.config.index_file_name

        # Strip extensions
        for ext in self.config.strip_extensions:
            if path.endswith(ext):
                path = path[: -len(ext)]
                break

        # Add .md extension
        if not path.endswith(".md"):
            last_segment = path.split("/")[-1] if "/" in path else path
            if "." not in last_segment:
                path = f"{path}/{self.config.index_file_name}"
            else:
                path = f"{path}{self.config.link_extension}"

        if not path.endswith(".md"):
            path = f"{path}.md"

        return f"/{path}"

    def _url_to_title(self, url: str) -> str:
        """Convert URL to readable title."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return "Home"

        segments = path.split("/")
        title = segments[-1]

        # Remove extension
        if "." in title:
            title = title.rsplit(".", 1)[0]

        return title.replace("-", " ").replace("_", " ").title()

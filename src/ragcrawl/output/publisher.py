"""Base publisher protocol."""

from abc import ABC, abstractmethod
from pathlib import Path

from ragcrawl.config.output_config import OutputConfig
from ragcrawl.models.document import Document


class MarkdownPublisher(ABC):
    """
    Abstract base class for markdown publishers.

    Publishers write crawled content to disk in configured formats.
    """

    def __init__(self, config: OutputConfig) -> None:
        """
        Initialize publisher.

        Args:
            config: Output configuration.
        """
        self.config = config
        self.output_path = Path(config.root_dir)

    @abstractmethod
    def publish(self, documents: list[Document]) -> list[Path]:
        """
        Publish documents to disk.

        Args:
            documents: Documents to publish.

        Returns:
            List of created file paths.
        """
        ...

    @abstractmethod
    def publish_single(self, document: Document) -> Path | None:
        """
        Publish a single document.

        Args:
            document: Document to publish.

        Returns:
            Created file path, or None if not written.
        """
        ...

    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_path.mkdir(parents=True, exist_ok=True)

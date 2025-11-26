"""Base exporter protocol."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document


class Exporter(ABC):
    """
    Abstract base class for content exporters.

    Exporters serialize documents and chunks for downstream pipelines.
    """

    @abstractmethod
    def export_document(self, document: Document, path: Path | None = None) -> str | None:
        """
        Export a single document.

        Args:
            document: Document to export.
            path: Optional file path to write to.

        Returns:
            Serialized document string, or None if written to file.
        """
        ...

    @abstractmethod
    def export_documents(
        self, documents: list[Document], path: Path
    ) -> None:
        """
        Export multiple documents to a file.

        Args:
            documents: Documents to export.
            path: File path to write to.
        """
        ...

    @abstractmethod
    def export_chunk(self, chunk: Chunk, path: Path | None = None) -> str | None:
        """
        Export a single chunk.

        Args:
            chunk: Chunk to export.
            path: Optional file path to write to.

        Returns:
            Serialized chunk string, or None if written to file.
        """
        ...

    @abstractmethod
    def export_chunks(self, chunks: list[Chunk], path: Path) -> None:
        """
        Export multiple chunks to a file.

        Args:
            chunks: Chunks to export.
            path: File path to write to.
        """
        ...

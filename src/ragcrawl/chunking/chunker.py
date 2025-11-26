"""Base chunker protocol."""

from abc import ABC, abstractmethod
from typing import Protocol

from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document


class ChunkerProtocol(Protocol):
    """Protocol for content chunkers."""

    def chunk(self, document: Document) -> list[Chunk]:
        """Chunk a document into segments."""
        ...


class Chunker(ABC):
    """
    Abstract base class for content chunkers.

    Chunkers split documents into segments optimized for
    embedding and retrieval in RAG pipelines.
    """

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk a document into segments.

        Args:
            document: Document to chunk.

        Returns:
            List of chunks.
        """
        ...

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate.

        Returns:
            Estimated token count.
        """
        ...

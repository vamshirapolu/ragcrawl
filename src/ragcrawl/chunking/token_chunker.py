"""Token-based chunker using tiktoken."""

from ragcrawl.chunking.chunker import Chunker
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document
from ragcrawl.utils.hashing import generate_chunk_id


class TokenChunker(Chunker):
    """
    Chunks content by token count.

    Uses tiktoken for accurate token counting and respects
    natural text boundaries (sentences, paragraphs).
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
        separators: list[str] | None = None,
    ) -> None:
        """
        Initialize token chunker.

        Args:
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Token overlap between chunks.
            encoding_name: Tiktoken encoding name.
            separators: Text separators to try, in order.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding_name = encoding_name
        self.separators = separators or ["\n\n", "\n", ". ", " "]

        self._encoding = None

    @property
    def encoding(self):
        """Get or create tiktoken encoding."""
        if self._encoding is None:
            try:
                import tiktoken
                self._encoding = tiktoken.get_encoding(self.encoding_name)
            except ImportError:
                self._encoding = None
        return self._encoding

    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk document by token count.

        Args:
            document: Document to chunk.

        Returns:
            List of chunks.
        """
        content = document.markdown
        if not content:
            return []

        # Split content into chunks
        text_chunks = self._split_text(content)

        # Create Chunk objects
        chunks = []
        current_offset = 0

        for i, text in enumerate(text_chunks):
            # Find actual offset in original content
            start_offset = content.find(text[:50], current_offset)
            if start_offset == -1:
                start_offset = current_offset
            end_offset = start_offset + len(text)
            current_offset = end_offset - self.chunk_overlap * 4  # Approximate

            chunk = Chunk(
                chunk_id=generate_chunk_id(document.doc_id, i),
                doc_id=document.doc_id,
                page_id=document.page_id,
                version_id=document.version_id,
                content=text,
                content_type="markdown",
                chunk_index=i,
                total_chunks=len(text_chunks),
                start_offset=start_offset,
                end_offset=end_offset,
                char_count=len(text),
                word_count=len(text.split()),
                token_estimate=self.estimate_tokens(text),
                section_path=None,
                heading=document.title,
                heading_level=None,
                source_url=document.source_url,
                title=document.title,
                chunker_type="token",
                overlap_tokens=self.chunk_overlap if i > 0 else 0,
            )
            chunks.append(chunk)

        return chunks

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks respecting token limits."""
        if self.estimate_tokens(text) <= self.chunk_size:
            return [text]

        chunks = []
        current_chunk: list[str] = []
        current_tokens = 0

        # Split by separators recursively
        segments = self._split_by_separator(text, 0)

        for segment in segments:
            segment_tokens = self.estimate_tokens(segment)

            if segment_tokens > self.chunk_size:
                # Segment too large, split further
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Force split large segment
                sub_chunks = self._force_split(segment)
                chunks.extend(sub_chunks)

            elif current_tokens + segment_tokens > self.chunk_size:
                # Would exceed limit, start new chunk
                if current_chunk:
                    chunks.append("".join(current_chunk))

                    # Handle overlap
                    if self.chunk_overlap > 0:
                        overlap_text = self._get_overlap(current_chunk)
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = self.estimate_tokens(overlap_text) if overlap_text else 0
                    else:
                        current_chunk = []
                        current_tokens = 0

                current_chunk.append(segment)
                current_tokens += segment_tokens

            else:
                current_chunk.append(segment)
                current_tokens += segment_tokens

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks

    def _split_by_separator(
        self, text: str, separator_index: int
    ) -> list[str]:
        """Recursively split text by separators."""
        if separator_index >= len(self.separators):
            return [text]

        separator = self.separators[separator_index]
        parts = text.split(separator)

        segments = []
        for i, part in enumerate(parts):
            if not part:
                continue

            # Add separator back except for last part
            if i < len(parts) - 1:
                part += separator

            # Check if part needs further splitting
            if self.estimate_tokens(part) > self.chunk_size:
                segments.extend(
                    self._split_by_separator(part, separator_index + 1)
                )
            else:
                segments.append(part)

        return segments

    def _force_split(self, text: str) -> list[str]:
        """Force split text that's too large for any separator."""
        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Estimate end position
            estimated_end = current_pos + (self.chunk_size * 4)  # ~4 chars per token
            end_pos = min(estimated_end, len(text))

            # Adjust to actual token count
            chunk_text = text[current_pos:end_pos]
            while self.estimate_tokens(chunk_text) > self.chunk_size and end_pos > current_pos + 10:
                end_pos -= 100
                chunk_text = text[current_pos:end_pos]

            chunks.append(chunk_text)
            current_pos = end_pos - (self.chunk_overlap * 4)  # Overlap

        return chunks

    def _get_overlap(self, current_chunk: list[str]) -> str:
        """Get overlap text from current chunk."""
        full_text = "".join(current_chunk)

        if self.chunk_overlap <= 0:
            return ""

        # Take last N tokens worth of text
        target_chars = self.chunk_overlap * 4
        return full_text[-target_chars:] if len(full_text) > target_chars else full_text

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count.

        Uses tiktoken if available, otherwise approximates.
        """
        if self.encoding:
            return len(self.encoding.encode(text))

        # Fallback: approximately 4 characters per token
        return len(text) // 4

"""Heading-aware markdown chunker."""

import re
from dataclasses import dataclass

from ragcrawl.chunking.chunker import Chunker
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document
from ragcrawl.utils.hashing import generate_chunk_id


@dataclass
class Section:
    """A section of content under a heading."""

    heading: str
    level: int
    content: str
    start_offset: int
    end_offset: int


class HeadingChunker(Chunker):
    """
    Chunks markdown content by headings.

    Creates chunks that respect document structure by splitting
    at heading boundaries while maintaining context.
    """

    def __init__(
        self,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        heading_levels: list[int] | None = None,
        include_heading_in_chunk: bool = True,
        overlap_size: int = 0,
    ) -> None:
        """
        Initialize heading chunker.

        Args:
            min_chunk_size: Minimum chunk size in characters.
            max_chunk_size: Maximum chunk size in characters.
            heading_levels: Heading levels to split on (default: [1, 2, 3]).
            include_heading_in_chunk: Include the heading in chunk content.
            overlap_size: Characters to overlap between chunks.
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.heading_levels = heading_levels or [1, 2, 3]
        self.include_heading_in_chunk = include_heading_in_chunk
        self.overlap_size = overlap_size

        # Regex for markdown headings
        self._heading_pattern = re.compile(
            r"^(#{1,6})\s+(.+?)$", re.MULTILINE
        )

    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk document by headings.

        Args:
            document: Document to chunk.

        Returns:
            List of chunks.
        """
        content = document.markdown
        if not content:
            return []

        # Parse sections
        sections = self._parse_sections(content)

        if not sections:
            # No headings found, treat as single chunk
            return self._create_single_chunk(document, content)

        # Create chunks from sections
        chunks = []
        section_path_stack: list[str] = []

        for i, section in enumerate(sections):
            # Update section path
            while section_path_stack and len(section_path_stack) >= section.level:
                section_path_stack.pop()
            section_path_stack.append(section.heading)
            section_path = " > ".join(section_path_stack)

            # Build chunk content
            if self.include_heading_in_chunk:
                chunk_content = f"{'#' * section.level} {section.heading}\n\n{section.content}"
            else:
                chunk_content = section.content

            # Handle oversized sections
            if len(chunk_content) > self.max_chunk_size:
                sub_chunks = self._split_large_section(
                    document,
                    chunk_content,
                    section,
                    section_path,
                    len(chunks),
                )
                chunks.extend(sub_chunks)
            elif len(chunk_content) >= self.min_chunk_size:
                chunk = self._create_chunk(
                    document=document,
                    content=chunk_content,
                    index=len(chunks),
                    start_offset=section.start_offset,
                    end_offset=section.end_offset,
                    section_path=section_path,
                    heading=section.heading,
                    heading_level=section.level,
                )
                chunks.append(chunk)
            # else: skip chunks that are too small

        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        return chunks

    def _parse_sections(self, content: str) -> list[Section]:
        """Parse content into sections by headings."""
        sections = []
        matches = list(self._heading_pattern.finditer(content))

        if not matches:
            return []

        for i, match in enumerate(matches):
            level = len(match.group(1))

            # Only split on configured heading levels
            if level not in self.heading_levels:
                continue

            heading = match.group(2).strip()
            start = match.start()

            # Find end of section (next heading or end of content)
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(content)

            # Extract section content (after heading)
            section_content = content[match.end():end].strip()

            sections.append(Section(
                heading=heading,
                level=level,
                content=section_content,
                start_offset=start,
                end_offset=end,
            ))

        return sections

    def _split_large_section(
        self,
        document: Document,
        content: str,
        section: Section,
        section_path: str,
        base_index: int,
    ) -> list[Chunk]:
        """Split an oversized section into smaller chunks."""
        chunks = []
        current_pos = 0
        chunk_index = base_index

        while current_pos < len(content):
            # Find split point
            end_pos = min(current_pos + self.max_chunk_size, len(content))

            if end_pos < len(content):
                # Try to split at paragraph boundary
                split_pos = content.rfind("\n\n", current_pos, end_pos)
                if split_pos == -1 or split_pos <= current_pos:
                    # Try sentence boundary
                    split_pos = content.rfind(". ", current_pos, end_pos)
                    if split_pos != -1:
                        split_pos += 1  # Include the period

                if split_pos != -1 and split_pos > current_pos:
                    end_pos = split_pos

            chunk_content = content[current_pos:end_pos].strip()

            if chunk_content:
                chunk = self._create_chunk(
                    document=document,
                    content=chunk_content,
                    index=chunk_index,
                    start_offset=section.start_offset + current_pos,
                    end_offset=section.start_offset + end_pos,
                    section_path=section_path,
                    heading=section.heading,
                    heading_level=section.level,
                )
                chunks.append(chunk)
                chunk_index += 1

            current_pos = end_pos

        return chunks

    def _create_single_chunk(
        self, document: Document, content: str
    ) -> list[Chunk]:
        """Create a single chunk for content without headings."""
        if len(content) <= self.max_chunk_size:
            chunk = self._create_chunk(
                document=document,
                content=content,
                index=0,
                start_offset=0,
                end_offset=len(content),
                section_path=None,
                heading=document.title,
                heading_level=None,
            )
            chunk.total_chunks = 1
            return [chunk]

        # Split large content
        chunks = []
        current_pos = 0

        while current_pos < len(content):
            end_pos = min(current_pos + self.max_chunk_size, len(content))

            if end_pos < len(content):
                split_pos = content.rfind("\n\n", current_pos, end_pos)
                if split_pos != -1 and split_pos > current_pos:
                    end_pos = split_pos

            chunk_content = content[current_pos:end_pos].strip()

            if chunk_content:
                chunk = self._create_chunk(
                    document=document,
                    content=chunk_content,
                    index=len(chunks),
                    start_offset=current_pos,
                    end_offset=end_pos,
                    section_path=None,
                    heading=document.title,
                    heading_level=None,
                )
                chunks.append(chunk)

            current_pos = end_pos

        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        return chunks

    def _create_chunk(
        self,
        document: Document,
        content: str,
        index: int,
        start_offset: int,
        end_offset: int,
        section_path: str | None,
        heading: str | None,
        heading_level: int | None,
    ) -> Chunk:
        """Create a chunk instance."""
        return Chunk(
            chunk_id=generate_chunk_id(document.doc_id, index),
            doc_id=document.doc_id,
            page_id=document.page_id,
            version_id=document.version_id,
            content=content,
            content_type="markdown",
            chunk_index=index,
            total_chunks=1,  # Updated after all chunks created
            start_offset=start_offset,
            end_offset=end_offset,
            char_count=len(content),
            word_count=len(content.split()),
            token_estimate=self.estimate_tokens(content),
            section_path=section_path,
            heading=heading,
            heading_level=heading_level,
            source_url=document.source_url,
            title=document.title,
            chunker_type="heading",
            overlap_tokens=0,
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (roughly 4 chars per token)."""
        return len(text) // 4

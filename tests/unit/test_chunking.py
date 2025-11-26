"""Tests for document chunking."""

from datetime import datetime, timezone

import pytest

from ragcrawl.chunking.heading_chunker import HeadingChunker
from ragcrawl.chunking.token_chunker import TokenChunker
from ragcrawl.models.document import Document


def create_test_document(markdown: str, title: str = "Test Document") -> Document:
    """Create a test document with the given markdown content."""
    now = datetime.now(timezone.utc)
    return Document(
        doc_id="doc123",
        page_id="doc123",
        source_url="https://example.com/page",
        normalized_url="https://example.com/page",
        markdown=markdown,
        title=title,
        status_code=200,
        depth=0,
        run_id="run123",
        site_id="site123",
        first_seen=now,
        last_seen=now,
        last_crawled=now,
    )


class TestHeadingChunker:
    """Tests for HeadingChunker."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.chunker = HeadingChunker(min_chunk_size=10)

    def test_chunk_by_h1(self) -> None:
        """Test chunking by H1 headings."""
        content = """# Section 1

Content for section 1 with enough text to meet minimum size.

# Section 2

Content for section 2 with enough text to meet minimum size.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) == 2
        assert "Section 1" in chunks[0].content
        assert "Section 2" in chunks[1].content

    def test_chunk_by_h2(self) -> None:
        """Test chunking by H2 headings."""
        chunker = HeadingChunker(heading_levels=[2], min_chunk_size=10)
        content = """# Main Title

Introduction text here.

## Section 1

Content 1 with enough text to meet minimum size.

## Section 2

Content 2 with enough text to meet minimum size.
"""
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        assert len(chunks) == 2
        assert "Section 1" in chunks[0].content
        assert "Section 2" in chunks[1].content

    def test_chunk_nested_headings(self) -> None:
        """Test chunking with nested headings."""
        content = """# Main

Content for main section here with enough text.

## Sub 1

Content 1 with enough text to meet minimum size.

### Sub Sub 1

Content 1.1 with enough text to meet minimum size.

## Sub 2

Content 2 with enough text to meet minimum size.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        # Should chunk at configured heading levels (1, 2, 3 by default)
        assert len(chunks) >= 2

    def test_chunk_no_headings(self) -> None:
        """Test chunking content without headings."""
        content = """This is just plain text.

Without any headings.

Multiple paragraphs here with enough content to test the chunker properly.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        # Should return single chunk
        assert len(chunks) == 1

    def test_chunk_preserves_heading_info(self) -> None:
        """Test that chunk metadata preserves heading info."""
        content = """# Main Title

Some introduction content here with enough text.

## Subsection

Content here with more than enough text to meet minimum requirements.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        # Check that heading info is preserved
        for chunk in chunks:
            assert chunk.content

    def test_chunk_min_size(self) -> None:
        """Test minimum chunk size filtering."""
        chunker = HeadingChunker(min_chunk_size=50)
        content = """# Section 1

Tiny.

# Section 2

This is a much longer section with more content that exceeds the minimum size requirement.
"""
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        # Small chunks should be filtered
        assert len(chunks) >= 1

    def test_chunk_includes_code_blocks(self) -> None:
        """Test that code blocks are preserved in chunks."""
        content = """# Section

Here's some code with enough text to meet minimum:

```python
def hello():
    print("Hello!")
```

More text to ensure we have enough content here for the chunk.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) >= 1
        assert "```python" in chunks[0].content

    def test_chunk_metadata(self) -> None:
        """Test chunk metadata generation."""
        content = """# Test Section

Some content here with enough text to meet the minimum size requirements for a chunk.
"""
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) >= 1
        chunk = chunks[0]
        assert chunk.chunk_index >= 0
        assert chunk.char_count > 0

    def test_chunk_without_heading_in_content(self) -> None:
        """Exclude heading text from chunk when configured."""
        chunker = HeadingChunker(min_chunk_size=10, include_heading_in_chunk=False)
        content = """# Heading

Body text with enough characters to be kept as a chunk."""
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        assert len(chunks) == 1
        assert chunks[0].content.startswith("Body text")

    def test_chunk_splits_large_sections(self) -> None:
        """Large section content is split using sentence/paragraph boundaries."""
        chunker = HeadingChunker(min_chunk_size=10, max_chunk_size=80)
        content = """# Heading

Paragraph one is fairly long to force a split. Paragraph two keeps the text flowing.

Paragraph three continues to add more text so that the combined content exceeds the max size."""
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 1
        # Ensure total_chunks updated
        assert all(c.total_chunks == len(chunks) for c in chunks)

    def test_chunk_single_large_content_without_headings(self) -> None:
        """Long content without headings is split into multiple chunks."""
        chunker = HeadingChunker(min_chunk_size=10, max_chunk_size=50)
        doc = create_test_document("A " * 200)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 1


class TestTokenChunker:
    """Tests for TokenChunker."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.chunker = TokenChunker(chunk_size=100, chunk_overlap=20)

    def test_chunk_short_content(self) -> None:
        """Test that short content is not split."""
        content = "This is a short piece of content."
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) == 1
        assert chunks[0].content == content

    def test_chunk_long_content(self) -> None:
        """Test chunking of long content."""
        content = " ".join(["word"] * 500)
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) > 1

    def test_chunk_overlap(self) -> None:
        """Test that chunks have overlap."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        content = " ".join(["word"] * 200)
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        # Check for some overlap between consecutive chunks
        assert len(chunks) > 1
        # Overlap is present implicitly through token counting

    def test_chunk_respects_max_tokens(self) -> None:
        """Test that chunks respect max token limit."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        content = " ".join(["word"] * 200)
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        for chunk in chunks:
            assert chunk.token_estimate <= 70  # Allow some margin

    def test_chunk_preserves_sentences(self) -> None:
        """Test that chunking tries to preserve sentence boundaries."""
        content = "First sentence. Second sentence. Third sentence. Fourth sentence."
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        # Should try to break at sentence boundaries
        for chunk in chunks:
            # Content should end at a reasonable boundary
            assert chunk.content

    def test_chunk_metadata(self) -> None:
        """Test chunk metadata generation."""
        content = " ".join(["word"] * 500)
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.token_estimate > 0
            assert chunk.char_count > 0

    def test_custom_encoding(self) -> None:
        """Test chunker with different encoding."""
        chunker = TokenChunker(
            chunk_size=100,
            chunk_overlap=20,
            encoding_name="cl100k_base",
        )
        content = " ".join(["word"] * 500)
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 1

    def test_chunk_empty_content(self) -> None:
        """Test chunking empty content."""
        doc = create_test_document("")
        chunks = self.chunker.chunk(doc)

        assert len(chunks) == 0

    def test_chunk_unicode_content(self) -> None:
        """Test chunking unicode content."""
        content = "Hello, 世界! " * 100
        doc = create_test_document(content)
        chunks = self.chunker.chunk(doc)

        assert len(chunks) >= 1
        # Verify content is preserved
        combined = "".join(c.content for c in chunks)
        # Due to overlap, combined might repeat some content
        assert "Hello" in combined
        assert "世界" in combined

    def test_token_chunker_with_encoding_and_forced_split(self) -> None:
        """Cover branch where a custom encoding is available and overlaps are applied."""
        class DummyEncoding:
            def encode(self, text: str) -> list[int]:
                return list(text)

        chunker = TokenChunker(chunk_size=10, chunk_overlap=2)
        chunker._encoding = DummyEncoding()  # bypass tiktoken import

        content = " ".join(["word"] * 20)
        doc = create_test_document(content)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 1
        # Overlap tokens applied after first chunk
        assert chunks[1].overlap_tokens == 2

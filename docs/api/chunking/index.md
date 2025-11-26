# Chunking API

ragcrawl provides chunking utilities to prepare content for embedding models.

## Overview

| Chunker | Description | Use Case |
|---------|-------------|----------|
| `HeadingChunker` | Splits by markdown headings | Preserve document structure |
| `TokenChunker` | Splits by token count | Fixed-size chunks for embeddings |

## HeadingChunker

Splits content at heading boundaries while respecting token limits.

### Usage

```python
from ragcrawl.chunking import HeadingChunker
from ragcrawl.models import Document

chunker = HeadingChunker(
    max_tokens=500,
    min_chunk_chars=100,
    heading_levels=[1, 2, 3],
)

# Chunk a single document
chunks = chunker.chunk(document)

# Chunk multiple documents
all_chunks = chunker.chunk_documents(documents)

for chunk in chunks:
    print(f"Section: {' > '.join(chunk.section_path)}")
    print(f"Tokens: ~{chunk.token_estimate}")
    print(chunk.content[:200])
    print()
```

### Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_tokens` | int | 500 | Maximum tokens per chunk |
| `min_chunk_chars` | int | 100 | Minimum characters for a chunk |
| `heading_levels` | list[int] | [1,2,3] | Heading levels to split on |
| `include_heading` | bool | True | Include heading in chunk |
| `preserve_code_blocks` | bool | True | Keep code blocks intact |

## TokenChunker

Splits content into fixed-size chunks by token count.

### Usage

```python
from ragcrawl.chunking import TokenChunker

chunker = TokenChunker(
    max_tokens=500,
    overlap_tokens=50,
    encoding_name="cl100k_base",
)

chunks = chunker.chunk(document)

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}")
    print(f"Tokens: {chunk.token_estimate}")
```

### Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_tokens` | int | 500 | Maximum tokens per chunk |
| `overlap_tokens` | int | 50 | Overlap between chunks |
| `encoding_name` | str | "cl100k_base" | Tokenizer encoding |

## Choosing a Chunker

### Use HeadingChunker when:

- Document has clear heading structure
- Semantic boundaries are important
- Context preservation matters
- Building hierarchical indexes

### Use TokenChunker when:

- Fixed chunk sizes needed
- Document lacks clear structure
- Maximum control over chunk boundaries
- Optimizing for specific embedding models

## Custom Chunking

Implement the `Chunker` protocol for custom logic:

```python
from ragcrawl.chunking import Chunker
from ragcrawl.models import Document, Chunk

class CustomChunker(Chunker):
    def chunk(self, document: Document) -> list[Chunk]:
        chunks = []
        # Your chunking logic here
        return chunks

    def chunk_documents(self, documents: list[Document]) -> list[Chunk]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks
```

## Integration with Embedding APIs

```python
from ragcrawl.chunking import HeadingChunker
import openai

chunker = HeadingChunker(max_tokens=500)
chunks = chunker.chunk_documents(documents)

# Prepare texts with context
texts = []
for chunk in chunks:
    # Add section context as prefix
    prefix = " > ".join(chunk.section_path) if chunk.section_path else ""
    text = f"[{prefix}]\n\n{chunk.content}" if prefix else chunk.content
    texts.append(text)

# Get embeddings
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input=texts,
)

# Store with metadata
for i, embedding in enumerate(response.data):
    store_vector(
        id=chunks[i].chunk_id,
        vector=embedding.embedding,
        metadata={
            "doc_id": chunks[i].doc_id,
            "section": chunks[i].section_path,
            "heading": chunks[i].heading,
        }
    )
```

## Module Reference

::: ragcrawl.chunking
    options:
      show_root_heading: false
      members:
        - HeadingChunker
        - TokenChunker
        - Chunker

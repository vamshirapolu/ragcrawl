# Chunk

The `Chunk` model represents a content chunk ready for embedding.

## Overview

`Chunk` is produced by chunkers and contains:

- The chunk content text
- Position information (index, total)
- Section context (heading path)
- Token estimates

## Usage

### Working with Chunks

Chunks are created by chunkers:

```python
from ragcrawl.chunking import HeadingChunker
from ragcrawl.models import Document

# Create a chunker
chunker = HeadingChunker(max_tokens=500)

# Chunk a document
chunks = chunker.chunk(document)

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}")
    print(f"Section: {' > '.join(chunk.section_path)}")
    print(f"Tokens: ~{chunk.token_estimate}")
    print(f"Content: {chunk.content[:100]}...")
    print()
```

### Chunk Metadata

```python
# Access chunk context
chunk = chunks[0]

# Document reference
print(f"From document: {chunk.doc_id}")

# Section path (breadcrumb)
print(f"Section: {chunk.section_path}")
# e.g., ["Getting Started", "Installation", "Requirements"]

# Current heading
print(f"Heading: {chunk.heading}")
# e.g., "Requirements"

# Position
print(f"Position: {chunk.chunk_index + 1} of {chunk.total_chunks}")
```

### Preparing for Embeddings

```python
# Prepare chunks for embedding API
for chunk in chunks:
    text = chunk.content

    # Add context prefix
    if chunk.section_path:
        context = " > ".join(chunk.section_path)
        text = f"[{context}]\n\n{text}"

    # Send to embedding API
    embedding = get_embedding(text)

    # Store with metadata
    store_embedding(
        embedding=embedding,
        metadata={
            "doc_id": chunk.doc_id,
            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.chunk_index,
            "section": chunk.section_path,
            "heading": chunk.heading,
        }
    )
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | str | Unique chunk identifier |
| `doc_id` | str | Source document ID |
| `content` | str | Chunk text content |
| `chunk_index` | int | Zero-based position |
| `total_chunks` | int | Total chunks in document |
| `section_path` | list[str] | Heading hierarchy |
| `heading` | str | Current section heading |
| `start_char` | int | Start character offset |
| `end_char` | int | End character offset |
| `char_count` | int | Character count |
| `token_estimate` | int | Estimated token count |

## API Reference

::: ragcrawl.models.chunk.Chunk
    options:
      show_root_heading: true

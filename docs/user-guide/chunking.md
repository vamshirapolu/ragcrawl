# Chunking Guide

Split documents into chunks optimized for RAG (Retrieval-Augmented Generation).

## Why Chunk?

LLMs have context limits. Chunking helps you:

- **Fit context windows**: Keep chunks under token limits
- **Improve retrieval**: Smaller, focused chunks match queries better
- **Preserve structure**: Maintain document hierarchy in chunks

## Chunking Strategies

### Heading-Based Chunking

Splits content at Markdown headings, preserving document structure:

```python
from ragcrawl.chunking.heading_chunker import HeadingChunker

chunker = HeadingChunker(
    min_level=1,        # Start splitting at H1
    max_level=3,        # Stop at H3 (don't split H4+)
    min_chunk_chars=100,  # Minimum chunk size
)

chunks = chunker.chunk(markdown_content)

for chunk in chunks:
    print(f"Heading: {' > '.join(chunk.heading_path)}")
    print(f"Content: {chunk.content[:100]}...")
    print()
```

Output:
```
Heading: Getting Started
Content: This guide helps you get started with...

Heading: Getting Started > Installation
Content: Install the package using pip...

Heading: Getting Started > Configuration
Content: Configure your settings in config.yaml...
```

### Token-Based Chunking

Splits content by token count with overlap:

```python
from ragcrawl.chunking.token_chunker import TokenChunker

chunker = TokenChunker(
    max_tokens=500,      # Maximum tokens per chunk
    overlap_tokens=50,   # Overlap between chunks
    encoding_name="cl100k_base",  # OpenAI tokenizer
)

chunks = chunker.chunk(content)

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}: {chunk.token_count} tokens")
```

## Chunking Documents

### Single Document

```python
from ragcrawl.models.document import Document
from ragcrawl.chunking.heading_chunker import HeadingChunker

doc = Document(
    doc_id="doc123",
    url="https://example.com/guide",
    title="User Guide",
    content="# Getting Started\n\n...",
    # ... other fields
)

chunker = HeadingChunker()
chunks = chunker.chunk(doc.content)

# Associate chunks with document
for chunk in chunks:
    chunk.doc_id = doc.doc_id
```

### Batch Processing

```python
from ragcrawl.chunking.heading_chunker import HeadingChunker

chunker = HeadingChunker()
all_chunks = []

for doc in documents:
    chunks = chunker.chunk(doc.content)
    for chunk in chunks:
        chunk.doc_id = doc.doc_id
        all_chunks.append(chunk)

print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
```

## Chunk Metadata

Each chunk includes metadata:

```python
from ragcrawl.models.chunk import Chunk

chunk = Chunk(
    chunk_id="chunk_abc123",
    doc_id="doc123",
    content="The actual chunk content...",
    chunk_index=0,           # Position in document
    char_count=500,          # Character count
    token_count=120,         # Token count (if computed)
    heading_path=["Guide", "Setup"],  # Heading hierarchy
)
```

## Configuration Examples

### For RAG Systems

Optimize for semantic search:

```python
# Heading-based for structured content
heading_chunker = HeadingChunker(
    min_level=2,          # Keep H1 content together
    max_level=3,
    min_chunk_chars=200,  # Avoid tiny chunks
)

# Token-based for unstructured content
token_chunker = TokenChunker(
    max_tokens=256,       # Smaller chunks for better matching
    overlap_tokens=30,    # Overlap for context continuity
)
```

### For Summarization

Larger chunks preserve more context:

```python
chunker = TokenChunker(
    max_tokens=1000,
    overlap_tokens=100,
)
```

### For Q&A

Balance chunk size and specificity:

```python
chunker = HeadingChunker(
    min_level=2,
    max_level=4,          # More granular splitting
    min_chunk_chars=100,
)
```

## Hybrid Chunking

Combine strategies for best results:

```python
from ragcrawl.chunking.heading_chunker import HeadingChunker
from ragcrawl.chunking.token_chunker import TokenChunker

# First split by headings
heading_chunker = HeadingChunker(max_level=2)
heading_chunks = heading_chunker.chunk(content)

# Then split large sections by tokens
token_chunker = TokenChunker(max_tokens=500, overlap_tokens=50)
final_chunks = []

for chunk in heading_chunks:
    if chunk.token_count > 500:
        # Split large sections
        sub_chunks = token_chunker.chunk(chunk.content)
        for sub in sub_chunks:
            sub.heading_path = chunk.heading_path
            final_chunks.append(sub)
    else:
        final_chunks.append(chunk)
```

## Exporting Chunks

### To JSON

```python
import json

chunks_data = [
    {
        "chunk_id": chunk.chunk_id,
        "doc_id": chunk.doc_id,
        "content": chunk.content,
        "heading_path": chunk.heading_path,
        "token_count": chunk.token_count,
    }
    for chunk in chunks
]

with open("chunks.json", "w") as f:
    json.dump(chunks_data, f, indent=2)
```

### To Vector Database Format

```python
# Format for Pinecone, Weaviate, etc.
vectors = []
for chunk in chunks:
    vectors.append({
        "id": chunk.chunk_id,
        "text": chunk.content,
        "metadata": {
            "doc_id": chunk.doc_id,
            "heading": " > ".join(chunk.heading_path or []),
            "char_count": chunk.char_count,
        },
    })
```

## Best Practices

1. **Match chunk size to your model**: GPT-4 handles larger chunks than smaller models
2. **Use overlap for continuity**: Prevents information loss at boundaries
3. **Preserve structure**: Heading paths help with retrieval and citation
4. **Test chunk quality**: Evaluate retrieval performance with your queries
5. **Consider content type**: Code needs different chunking than prose

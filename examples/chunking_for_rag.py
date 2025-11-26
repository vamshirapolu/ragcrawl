#!/usr/bin/env python3
"""
Chunking example for RAG (Retrieval-Augmented Generation).

This example demonstrates how to:
1. Crawl content
2. Chunk it for embedding
3. Export in a format suitable for vector databases
"""

import asyncio
import json
from pathlib import Path
from typing import List

from ragcrawl.chunking.heading_chunker import HeadingChunker
from ragcrawl.chunking.token_chunker import TokenChunker
from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.core.crawl_job import CrawlJob
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.document import Document


def chunk_documents_by_heading(documents: List[Document]) -> List[Chunk]:
    """Chunk documents by heading structure."""

    chunker = HeadingChunker(
        min_level=1,        # Start at H1
        max_level=3,        # Go down to H3
        min_chunk_chars=100,  # Minimum chunk size
    )

    all_chunks = []

    for doc in documents:
        chunks = chunker.chunk(doc.content)

        # Associate chunks with source document
        for chunk in chunks:
            chunk.doc_id = doc.doc_id
            # Add source URL to metadata
            chunk.metadata = {
                "url": doc.url,
                "title": doc.title,
            }
            all_chunks.append(chunk)

    return all_chunks


def chunk_documents_by_tokens(documents: List[Document]) -> List[Chunk]:
    """Chunk documents by token count."""

    chunker = TokenChunker(
        max_tokens=256,      # Small chunks for better retrieval
        overlap_tokens=30,   # Some overlap for context
        encoding_name="cl100k_base",  # OpenAI tokenizer
    )

    all_chunks = []

    for doc in documents:
        chunks = chunker.chunk(doc.content)

        for chunk in chunks:
            chunk.doc_id = doc.doc_id
            chunk.metadata = {
                "url": doc.url,
                "title": doc.title,
            }
            all_chunks.append(chunk)

    return all_chunks


def export_for_vector_db(chunks: List[Chunk], documents: List[Document], output_path: Path):
    """Export chunks in a format ready for vector databases."""

    # Create document lookup
    doc_map = {doc.doc_id: doc for doc in documents}

    records = []
    for chunk in chunks:
        doc = doc_map.get(chunk.doc_id)
        if not doc:
            continue

        record = {
            "id": chunk.chunk_id,
            "text": chunk.content,
            "metadata": {
                "doc_id": chunk.doc_id,
                "url": doc.url,
                "title": doc.title,
                "heading_path": " > ".join(chunk.heading_path) if chunk.heading_path else None,
                "chunk_index": chunk.chunk_index,
                "char_count": chunk.char_count,
                "token_count": chunk.token_count,
            },
        }
        records.append(record)

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2, default=str)

    print(f"Exported {len(records)} chunks to {output_path}")


async def main():
    """Run the chunking example."""

    # Configure crawl
    config = CrawlerConfig(
        seeds=["https://docs.python.org/3/tutorial/introduction.html"],
        max_pages=5,
        max_depth=1,
        storage=StorageConfig(
            backend=DuckDBConfig(path="./chunking_example.duckdb")
        ),
    )

    print("Crawling content...")
    job = CrawlJob(config)
    result = await job.run()

    if not result.success:
        print(f"Crawl failed: {result.error}")
        return

    print(f"Crawled {len(result.documents)} documents")

    # Heading-based chunking
    print("\n--- Heading-Based Chunking ---")
    heading_chunks = chunk_documents_by_heading(result.documents)
    print(f"Created {len(heading_chunks)} chunks")

    if heading_chunks:
        print("\nSample chunks:")
        for chunk in heading_chunks[:3]:
            heading = " > ".join(chunk.heading_path) if chunk.heading_path else "No heading"
            print(f"  [{heading}]")
            print(f"    {chunk.content[:100]}...")
            print()

    # Token-based chunking
    print("\n--- Token-Based Chunking ---")
    token_chunks = chunk_documents_by_tokens(result.documents)
    print(f"Created {len(token_chunks)} chunks")

    if token_chunks:
        print("\nSample chunks:")
        for chunk in token_chunks[:3]:
            print(f"  [Chunk {chunk.chunk_index}, {chunk.token_count} tokens]")
            print(f"    {chunk.content[:100]}...")
            print()

    # Export for vector database
    print("\n--- Exporting ---")
    export_for_vector_db(
        heading_chunks,
        result.documents,
        Path("./chunks_heading.json")
    )
    export_for_vector_db(
        token_chunks,
        result.documents,
        Path("./chunks_token.json")
    )


if __name__ == "__main__":
    asyncio.run(main())

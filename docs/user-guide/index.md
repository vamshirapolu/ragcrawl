# User Guide

This guide covers the core functionality of ragcrawl in detail.

## Overview

ragcrawl provides a complete pipeline for converting websites into LLM-ready knowledge bases:

```mermaid
graph LR
    A[Web Pages] --> B[Fetcher]
    B --> C[Extractor]
    C --> D[Storage]
    D --> E[Chunker]
    E --> F[Exporter]
    F --> G[Output Files]
```

## Guide Contents

### [Crawling Websites](crawling.md)

Learn how to crawl websites effectively:

- Starting a basic crawl
- Configuring URL filters
- Handling JavaScript-rendered content
- Respecting robots.txt and rate limits
- Managing large-scale crawls

### [Incremental Sync](syncing.md)

Keep your knowledge base up-to-date:

- Understanding sync strategies
- Using sitemaps for efficient updates
- Conditional requests with ETags
- Content change detection
- Handling deleted pages

### [Chunking Content](chunking.md)

Prepare content for embedding models:

- Heading-aware chunking
- Token-based chunking
- Configuring chunk sizes
- Preserving context in chunks
- Metadata in chunks

### [Exporting Data](exporting.md)

Export your crawled data:

- JSON and JSONL formats
- Single-page combined output
- Multi-page with preserved structure
- Link rewriting for local files
- Custom export formats

## Common Workflows

### Documentation Site to RAG

```python
from ragcrawl import CrawlJob, CrawlerConfig

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=500,
    include_patterns=["/docs/*"],
)

job = CrawlJob(config)
result = await job.run()

# Chunk for embeddings
from ragcrawl.chunking import HeadingChunker
chunker = HeadingChunker(max_tokens=500)
chunks = chunker.chunk_documents(result.documents)
```

### Keep Knowledge Base Fresh

```python
from ragcrawl import SyncJob, SyncConfig

config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
    use_conditional_requests=True,
)

job = SyncJob(config)
result = await job.run()

print(f"Updated: {result.stats.pages_changed}")
print(f"New: {result.stats.pages_new}")
print(f"Deleted: {result.stats.pages_deleted}")
```

## Best Practices

!!! tip "Start Small"
    Begin with a small `max_pages` limit to test your configuration before crawling an entire site.

!!! tip "Use Include Patterns"
    Focus your crawl on relevant content with `include_patterns` to avoid noise.

!!! tip "Enable Caching"
    Use DuckDB storage to enable efficient incremental syncs.

!!! warning "Respect Rate Limits"
    Always configure appropriate delays between requests to avoid overloading target servers.

## Next Steps

- [Configuration Reference](../configuration/index.md) - All configuration options
- [CLI Reference](../cli/index.md) - Command-line usage
- [API Reference](../api/index.md) - Python API documentation

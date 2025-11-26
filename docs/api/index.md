# API Reference

Complete Python API documentation for ragcrawl.

## Overview

ragcrawl is organized into the following modules:

| Module | Description |
|--------|-------------|
| [Core](core/index.md) | Main entry points (CrawlJob, SyncJob) |
| [Models](models/index.md) | Data models (Document, Page, Chunk, etc.) |
| [Storage](storage/index.md) | Storage backends (DuckDB, DynamoDB) |
| [Chunking](chunking/index.md) | Content chunking (HeadingChunker, TokenChunker) |
| [Export](export/index.md) | Export and publishing (JSON, Markdown) |
| [Filters](filters/index.md) | URL filtering and normalization |

## Quick Reference

### Crawling

```python
import asyncio
from ragcrawl import CrawlJob
from ragcrawl.config import CrawlerConfig

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
    max_depth=5,
)

job = CrawlJob(config)
result = asyncio.run(job.run())

print(f"Crawled {result.stats.pages_crawled} pages")
```

### Syncing

```python
import asyncio
from ragcrawl import SyncJob
from ragcrawl.config import SyncConfig

config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
)

job = SyncJob(config)
result = asyncio.run(job.run())

print(f"Updated {result.stats.pages_changed} pages")
```

### Chunking

```python
from ragcrawl.chunking import HeadingChunker

chunker = HeadingChunker(max_tokens=500)
chunks = chunker.chunk_documents(result.documents)
```

### Exporting

```python
from ragcrawl.export import JSONLExporter
from pathlib import Path

exporter = JSONLExporter()
exporter.export_documents(result.documents, Path("output.jsonl"))
```

## Module Documentation

<div class="grid cards" markdown>

-   :material-play-circle:{ .lg .middle } **[Core](core/index.md)**

    ---

    `CrawlJob` and `SyncJob` - main entry points for crawling operations.

-   :material-cube-outline:{ .lg .middle } **[Models](models/index.md)**

    ---

    Data models: `Document`, `Page`, `PageVersion`, `Chunk`, `Site`, `CrawlRun`

-   :material-database:{ .lg .middle } **[Storage](storage/index.md)**

    ---

    Storage backends: `DuckDBBackend`, `DynamoDBBackend`

-   :material-content-cut:{ .lg .middle } **[Chunking](chunking/index.md)**

    ---

    Content chunkers: `HeadingChunker`, `TokenChunker`

-   :material-export:{ .lg .middle } **[Export](export/index.md)**

    ---

    Exporters and publishers: `JSONExporter`, `SinglePagePublisher`, `MultiPagePublisher`

-   :material-filter:{ .lg .middle } **[Filters](filters/index.md)**

    ---

    URL filtering: `LinkFilter`, `PatternMatcher`, `URLNormalizer`

</div>

## Configuration Classes

| Class | Module | Description |
|-------|--------|-------------|
| `CrawlerConfig` | `ragcrawl.config` | Crawl settings |
| `SyncConfig` | `ragcrawl.config` | Sync settings |
| `StorageConfig` | `ragcrawl.config` | Storage backend config |
| `OutputConfig` | `ragcrawl.config` | Output format config |
| `DuckDBConfig` | `ragcrawl.config.storage_config` | DuckDB settings |
| `DynamoDBConfig` | `ragcrawl.config.storage_config` | DynamoDB settings |

## Imports

```python
# Main classes
from ragcrawl import CrawlJob, SyncJob
from ragcrawl.config import CrawlerConfig, SyncConfig

# Storage
from ragcrawl.config.storage_config import StorageConfig, DuckDBConfig, DynamoDBConfig
from ragcrawl.storage import create_storage_backend

# Models
from ragcrawl.models import Document, Page, PageVersion, Chunk, Site, CrawlRun

# Chunking
from ragcrawl.chunking import HeadingChunker, TokenChunker

# Export
from ragcrawl.export import JSONExporter, JSONLExporter
from ragcrawl.output import SinglePagePublisher, MultiPagePublisher

# Filters
from ragcrawl.filters import LinkFilter, PatternMatcher, URLNormalizer
```

## Type Hints

ragcrawl is fully typed. Enable type checking in your IDE:

```python
from ragcrawl import CrawlJob
from ragcrawl.config import CrawlerConfig

config: CrawlerConfig = CrawlerConfig(...)
job: CrawlJob = CrawlJob(config)
```

## Async API

Core operations are async:

```python
import asyncio

async def main():
    job = CrawlJob(config)
    result = await job.run()
    return result

result = asyncio.run(main())
```

Or use the sync wrapper:

```python
from ragcrawl import CrawlJob

job = CrawlJob(config)
result = asyncio.run(job.run())
```

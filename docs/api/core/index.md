# Core API

The core module contains the main entry points for crawling and syncing.

## Overview

| Class | Description |
|-------|-------------|
| [CrawlJob](crawl-job.md) | Execute website crawls |
| [SyncJob](sync-job.md) | Incremental sync operations |

## Quick Start

### Crawling

```python
import asyncio
from ragcrawl.config import CrawlerConfig
from ragcrawl.core import CrawlJob

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
)

job = CrawlJob(config)
result = asyncio.run(job.run())

print(f"Crawled {result.stats.pages_crawled} pages")
```

### Syncing

```python
import asyncio
from ragcrawl.config import SyncConfig
from ragcrawl.core import SyncJob

config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
)

job = SyncJob(config)
result = asyncio.run(job.run())

print(f"Updated {result.stats.pages_changed} pages")
```

## Module Reference

::: ragcrawl.core
    options:
      show_root_heading: false
      members:
        - CrawlJob
        - SyncJob

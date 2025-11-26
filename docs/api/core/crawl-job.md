# CrawlJob

The `CrawlJob` class is the main entry point for crawling websites.

## Overview

`CrawlJob` orchestrates the entire crawling process:

1. Initializes the storage backend
2. Creates or retrieves the site record
3. Manages the URL frontier
4. Coordinates fetching, extraction, and storage
5. Tracks statistics and handles errors

## Usage

### Basic Crawl

```python
import asyncio
from ragcrawl.config import CrawlerConfig
from ragcrawl.core import CrawlJob

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
    max_depth=5,
)

job = CrawlJob(config)
result = asyncio.run(job.run())

# Access results
print(f"Pages crawled: {result.stats.pages_crawled}")
print(f"Pages failed: {result.stats.pages_failed}")

for doc in result.documents:
    print(f"- {doc.title}: {doc.source_url}")
```

### With Callbacks

```python
from ragcrawl.hooks import CrawlCallbacks

class MyCallbacks(CrawlCallbacks):
    def on_page_crawled(self, page, version):
        print(f"Crawled: {page.url}")

    def on_page_error(self, url, error):
        print(f"Error: {url} - {error}")

job = CrawlJob(config, callbacks=MyCallbacks())
result = asyncio.run(job.run())
```

### Graceful Stop

```python
import asyncio
import signal

job = CrawlJob(config)

def handle_signal(sig, frame):
    asyncio.create_task(job.stop())

signal.signal(signal.SIGINT, handle_signal)

result = asyncio.run(job.run())
```

## Configuration

See [CrawlerConfig](../../configuration/crawler.md) for all options.

Key options:

| Option | Type | Description |
|--------|------|-------------|
| `seeds` | list[str] | Starting URLs |
| `max_pages` | int | Maximum pages to crawl |
| `max_depth` | int | Maximum link depth |
| `delay_seconds` | float | Delay between requests |
| `include_patterns` | list[str] | URL patterns to include |
| `exclude_patterns` | list[str] | URL patterns to exclude |

## API Reference

::: ragcrawl.core.crawl_job.CrawlJob
    options:
      show_root_heading: true
      members:
        - __init__
        - run
        - stop

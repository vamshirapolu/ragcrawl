# SyncJob

The `SyncJob` class handles incremental updates to previously crawled sites.

## Overview

`SyncJob` efficiently updates your knowledge base by:

1. Checking sitemap for new/updated URLs
2. Using conditional requests (ETags, Last-Modified)
3. Comparing content hashes for changes
4. Marking deleted pages as tombstones

## Usage

### Basic Sync

```python
import asyncio
from ragcrawl.config import SyncConfig
from ragcrawl.core import SyncJob

config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
    use_conditional_requests=True,
)

job = SyncJob(config)
result = asyncio.run(job.run())

# Check what changed
print(f"New pages: {result.stats.pages_new}")
print(f"Updated pages: {result.stats.pages_changed}")
print(f"Deleted pages: {result.stats.pages_deleted}")
print(f"Unchanged: {result.stats.pages_unchanged}")
```

### Sync with Age Filter

Only sync pages that haven't been checked recently:

```python
config = SyncConfig(
    site_id="site_abc123",
    max_age_hours=24,  # Only pages not synced in 24 hours
)

job = SyncJob(config)
result = asyncio.run(job.run())
```

### Sync with Page Limit

```python
config = SyncConfig(
    site_id="site_abc123",
    max_pages=100,  # Stop after 100 pages
)

job = SyncJob(config)
result = asyncio.run(job.run())
```

## Sync Strategies

SyncJob uses multiple strategies in order of efficiency:

### 1. Sitemap

If available, the sitemap provides:
- List of all current URLs
- Last modification dates
- Change frequency hints

```python
config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,  # Default: True
)
```

### 2. Conditional Requests

Uses HTTP headers to avoid downloading unchanged content:

```python
config = SyncConfig(
    site_id="site_abc123",
    use_conditional_requests=True,  # Default: True
)
```

Supports:
- `If-None-Match` with ETags
- `If-Modified-Since` with Last-Modified dates

### 3. Content Hash Comparison

As a fallback, compares content hashes:

```python
# This happens automatically when conditional requests
# don't indicate a change but content differs
```

## Configuration

See [SyncConfig](../../configuration/crawler.md#syncconfig) for all options.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `site_id` | str | required | Site to sync |
| `max_pages` | int | None | Maximum pages to sync |
| `max_age_hours` | float | None | Only sync pages older than N hours |
| `use_sitemap` | bool | True | Use sitemap for discovery |
| `use_conditional_requests` | bool | True | Use ETags/Last-Modified |

## API Reference

::: ragcrawl.core.sync_job.SyncJob
    options:
      show_root_heading: true
      members:
        - __init__
        - run
        - stop

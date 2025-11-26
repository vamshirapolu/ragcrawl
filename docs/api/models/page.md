# Page

The `Page` model tracks the state and freshness of crawled pages.

## Overview

`Page` is an internal model that tracks:

- Page URL and identification
- Current content version
- Freshness information (ETags, Last-Modified)
- Crawl metadata (depth, status, errors)

## Usage

### Accessing Pages

```python
from ragcrawl.storage import create_storage_backend

backend = create_storage_backend(storage_config)
backend.initialize()

# Get a specific page
page = backend.get_page(page_id)
print(f"URL: {page.url}")
print(f"Last crawled: {page.last_crawled}")
print(f"Status: {page.status_code}")

# Get page by URL
page = backend.get_page_by_url(site_id, url)

# List all pages for a site
pages = backend.list_pages(site_id)
for page in pages:
    print(f"{page.url}: {page.status_code}")
```

### Page Freshness

```python
# Check if page needs re-crawling
from datetime import datetime, timezone, timedelta

max_age = timedelta(hours=24)
if page.last_crawled < datetime.now(timezone.utc) - max_age:
    print(f"Page {page.url} needs refresh")

# Check using conditional request headers
if page.etag:
    headers = {"If-None-Match": page.etag}
if page.last_modified:
    headers = {"If-Modified-Since": page.last_modified}
```

### Tombstone Pages

```python
# Check if page was deleted
if page.is_tombstone:
    print(f"Page {page.url} was removed from site")

# Get pages including tombstones
pages = backend.list_pages(site_id, include_tombstones=True)
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `page_id` | str | Unique page identifier |
| `site_id` | str | Parent site ID |
| `url` | str | Page URL |
| `canonical_url` | str | Canonical URL if different |
| `current_version_id` | str | Current content version |
| `content_hash` | str | Content hash for change detection |
| `etag` | str | HTTP ETag header |
| `last_modified` | str | HTTP Last-Modified header |
| `first_seen` | datetime | First crawl time |
| `last_seen` | datetime | Last seen in crawl |
| `last_crawled` | datetime | Last successful crawl |
| `last_changed` | datetime | Last content change |
| `depth` | int | Link depth from seed |
| `referrer_url` | str | Referring page URL |
| `status_code` | int | Last HTTP status |
| `is_tombstone` | bool | Page was deleted |
| `error_count` | int | Consecutive errors |
| `last_error` | str | Last error message |
| `version_count` | int | Total versions |

## API Reference

::: ragcrawl.models.page.Page
    options:
      show_root_heading: true

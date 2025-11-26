# Site

The `Site` model represents a crawled website and its configuration.

## Overview

`Site` stores:

- Site identification (ID, name)
- Seed URLs for crawling
- Domain restrictions
- Crawl statistics
- Timestamps

## Usage

### Creating a Site

Sites are typically created automatically during crawling:

```python
from datetime import datetime, timezone
from ragcrawl.models import Site

site = Site(
    site_id="site_abc123",
    name="Example Documentation",
    seeds=["https://docs.example.com"],
    allowed_domains=["docs.example.com"],
    allowed_subdomains=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)
```

### Accessing Site Data

```python
# Get basic info
print(f"Site: {site.name}")
print(f"ID: {site.site_id}")
print(f"Seeds: {site.seeds}")

# Get statistics
print(f"Total pages: {site.total_pages}")
print(f"Total runs: {site.total_runs}")

# Check timestamps
print(f"Created: {site.created_at}")
print(f"Last crawl: {site.last_crawl_at}")
```

### Listing Sites

```python
from ragcrawl.storage import create_storage_backend

backend = create_storage_backend(storage_config)
backend.initialize()

sites = backend.list_sites()
for site in sites:
    print(f"{site.site_id}: {site.name} ({site.total_pages} pages)")
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | str | Unique site identifier |
| `name` | str | Human-readable name |
| `seeds` | list[str] | Starting URLs |
| `allowed_domains` | list[str] | Domains to crawl |
| `allowed_subdomains` | bool | Allow subdomains |
| `config` | dict | Configuration snapshot |
| `created_at` | datetime | Creation time |
| `updated_at` | datetime | Last update time |
| `last_crawl_at` | datetime | Last crawl time |
| `last_sync_at` | datetime | Last sync time |
| `total_pages` | int | Total pages crawled |
| `total_runs` | int | Total crawl runs |
| `is_active` | bool | Site is active |

## API Reference

::: ragcrawl.models.site.Site
    options:
      show_root_heading: true

# Syncing Guide

Keep your knowledge base up-to-date with incremental syncing.

## How Sync Works

The sync process efficiently updates your knowledge base:

1. **Sitemap Check**: Parse sitemap.xml for recently changed URLs
2. **Conditional Requests**: Use ETag/Last-Modified headers
3. **Content Hashing**: Compare content hashes to detect changes
4. **Tombstones**: Mark deleted pages (404/410 responses)

## Basic Sync

### CLI

```bash
# Find your site ID
ragcrawl sites

# Sync the site
ragcrawl sync site_abc123

# Sync with options
ragcrawl sync site_abc123 \
    --max-pages 500 \
    --max-age 24 \
    --output ./updates \
    --verbose
```

### CLI Options Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--storage` | `-s` | DuckDB storage path (default: `~/.ragcrawl/ragcrawl.duckdb`) |
| `--max-pages` | `-m` | Maximum pages to sync |
| `--max-age` | | Only check pages older than N hours |
| `--output` | `-o` | Output directory for updates |
| `--verbose` | `-v` | Verbose output |

### Listing Sites and Runs

Before syncing, you may need to find your site ID:

```bash
# List all crawled sites
ragcrawl sites

# List all crawl runs
ragcrawl list

# List runs for a specific site
ragcrawl runs site_abc123 --limit 10

# Filter runs by status
ragcrawl list --status completed
ragcrawl list --site site_abc123
```

### Python API

```python
import asyncio
from ragcrawl.config.sync_config import SyncConfig
from ragcrawl.core.sync_job import SyncJob

async def sync_site():
    config = SyncConfig(
        site_id="site_abc123",
    )

    job = SyncJob(config)
    result = await job.run()

    if result.success:
        print(f"Checked: {result.stats.pages_crawled}")
        print(f"Changed: {result.stats.pages_changed}")
        print(f"Deleted: {result.stats.pages_deleted}")

asyncio.run(sync_site())
```

## Sync Strategies

### Sitemap-Based (Fastest)

Prioritizes pages listed in sitemap.xml with recent lastmod dates:

```python
config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
    sitemap_url="https://example.com/sitemap.xml",  # Auto-detected if not specified
)
```

### Conditional Headers

Uses HTTP caching headers to skip unchanged content:

```python
config = SyncConfig(
    site_id="site_abc123",
    use_conditional_requests=True,  # Default: True
)
```

The crawler sends:
- `If-None-Match: <etag>` if ETag is stored
- `If-Modified-Since: <date>` if Last-Modified is stored

304 Not Modified responses are skipped efficiently.

### Content Hash Diffing

Compares content hashes for pages without caching headers:

```python
config = SyncConfig(
    site_id="site_abc123",
    use_hash_diffing=True,  # Default: True
)
```

## Sync Options

### Page Limits

```python
config = SyncConfig(
    site_id="site_abc123",
    max_pages=500,  # Maximum pages to check
)
```

### Age-Based Filtering

Only check pages older than a certain age:

```python
config = SyncConfig(
    site_id="site_abc123",
    max_age_hours=24,  # Only check pages not synced in last 24 hours
)
```

### Priority-Based Selection

Check high-priority pages first:

```python
config = SyncConfig(
    site_id="site_abc123",
    priority_patterns=[
        r"/docs/.*",      # Check docs first
        r"/api/.*",       # Then API docs
    ],
)
```

## Handling Changes

### Change Events

Subscribe to change events during sync:

```python
from ragcrawl.export.events import EventEmitter, ChangeEvent

emitter = EventEmitter()

@emitter.on("page_changed")
def handle_change(event: ChangeEvent):
    print(f"Changed: {event.url}")
    print(f"  Old hash: {event.old_hash}")
    print(f"  New hash: {event.new_hash}")

@emitter.on("page_deleted")
def handle_deletion(event: ChangeEvent):
    print(f"Deleted: {event.url}")

config = SyncConfig(
    site_id="site_abc123",
    event_emitter=emitter,
)
```

### Output Changes Only

Export only changed content:

```python
from ragcrawl.config.output_config import OutputConfig, OutputMode

config = SyncConfig(
    site_id="site_abc123",
    output=OutputConfig(
        mode=OutputMode.MULTI,
        root_dir="./updates",
    ),
)

job = SyncJob(config)
result = await job.run()

# result.changed_pages contains list of changed URLs
# result.documents contains only changed documents
```

## Tombstones

Pages returning 404 or 410 are marked as "tombstones":

```python
# Check for tombstones
from ragcrawl.storage.backend import create_storage_backend

backend = create_storage_backend(storage_config)
pages = backend.list_pages(site_id)

for page in pages:
    if page.is_tombstone:
        print(f"Deleted page: {page.url}")
```

## Sync Scheduling

### Manual Scheduling

```bash
# Run via cron
0 * * * * cd /app && ragcrawl sync site_abc123 >> /var/log/sync.log 2>&1
```

### Python Scheduler

```python
import asyncio
from datetime import datetime

async def scheduled_sync():
    while True:
        print(f"Starting sync at {datetime.now()}")

        config = SyncConfig(site_id="site_abc123")
        job = SyncJob(config)
        result = await job.run()

        if result.stats.pages_changed > 0:
            print(f"Updated {result.stats.pages_changed} pages")

        # Wait 1 hour
        await asyncio.sleep(3600)

asyncio.run(scheduled_sync())
```

## Complete Example

```python
import asyncio
from ragcrawl.config.sync_config import SyncConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.core.sync_job import SyncJob
from ragcrawl.export.events import EventEmitter

async def sync_and_export():
    # Set up event handling
    emitter = EventEmitter()

    @emitter.on("page_changed")
    def on_change(event):
        print(f"📝 Updated: {event.url}")

    @emitter.on("page_deleted")
    def on_delete(event):
        print(f"🗑️ Deleted: {event.url}")

    config = SyncConfig(
        site_id="site_abc123",

        # Sync options
        max_pages=1000,
        max_age_hours=24,
        use_sitemap=True,
        use_conditional_requests=True,

        # Storage
        storage=StorageConfig(
            backend=DuckDBConfig(path="./crawler.duckdb")
        ),

        # Output changes
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./updates",
        ),

        event_emitter=emitter,
    )

    job = SyncJob(config)
    result = await job.run()

    print(f"\nSync Summary:")
    print(f"  Pages checked: {result.stats.pages_crawled}")
    print(f"  Pages changed: {result.stats.pages_changed}")
    print(f"  Pages deleted: {result.stats.pages_deleted}")
    print(f"  Duration: {result.duration_seconds:.1f}s")

    if result.changed_pages:
        print(f"\nChanged pages:")
        for url in result.changed_pages[:10]:
            print(f"  - {url}")

asyncio.run(sync_and_export())
```

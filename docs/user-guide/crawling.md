# Crawling Guide

This guide covers all aspects of crawling websites with ragcrawl.

## How Crawling Works

1. **Seed URLs**: The crawler starts from one or more seed URLs
2. **Fetch**: Each page is fetched via HTTP or browser rendering
3. **Extract**: Content is converted to Markdown, links are extracted
4. **Filter**: Links are filtered based on domain, patterns, and depth
5. **Queue**: New links are added to the priority queue (frontier)
6. **Store**: Page content and metadata are stored
7. **Repeat**: Process continues until limits are reached

## CLI Usage

### Basic Crawl

```bash
ragcrawl crawl https://docs.example.com
```

### Full Options

```bash
ragcrawl crawl https://docs.example.com \
    --max-pages 500 \
    --max-depth 10 \
    --output ./output \
    --output-mode multi \
    --storage ./crawler.duckdb \
    --include "/docs/.*" \
    --exclude "/admin/.*" \
    --robots \
    --js \
    --export-json ./docs.json \
    --export-jsonl ./docs.jsonl \
    --verbose
```

### CLI Options Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--max-pages` | `-m` | Maximum pages to crawl (default: from config) |
| `--max-depth` | `-d` | Maximum crawl depth (default: from config) |
| `--output` | `-o` | Output directory |
| `--output-mode` | | `single` or `multi` page output |
| `--storage` | `-s` | DuckDB storage path (default: `~/.ragcrawl/ragcrawl.duckdb`) |
| `--include` | `-i` | Include URL patterns (regex, repeatable) |
| `--exclude` | `-e` | Exclude URL patterns (regex, repeatable) |
| `--robots/--no-robots` | | Respect robots.txt (default: enabled) |
| `--js/--no-js` | | Enable JavaScript rendering |
| `--export-json` | | Export documents to JSON file |
| `--export-jsonl` | | Export documents to JSONL file |
| `--markdown-config` | | Path to MarkdownConfig overrides (TOML/JSON) |
| `--verbose` | `-v` | Verbose output |

### Multiple Seeds

You can specify multiple seed URLs:

```bash
ragcrawl crawl https://docs.example.com https://api.example.com
```

## Crawl Modes

### HTTP Mode (Default)

Fast crawling using HTTP requests. Best for static sites:

```python
from ragcrawl.config.crawler_config import CrawlerConfig, FetchMode

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    fetch_mode=FetchMode.HTTP,
)
```

### Browser Mode

Uses headless Chromium for JavaScript-heavy sites:

```python
config = CrawlerConfig(
    seeds=["https://app.example.com"],
    fetch_mode=FetchMode.BROWSER,
)
```

CLI:
```bash
ragcrawl crawl https://app.example.com --js
```

### Hybrid Mode

Tries HTTP first, falls back to browser on failure:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    fetch_mode=FetchMode.HYBRID,
)
```

## URL Filtering

### Domain Restrictions

By default, the crawler stays within the seed domains:

```python
config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    allowed_domains=["docs.example.com", "api.example.com"],
    allow_subdomains=True,  # Also allows sub.docs.example.com
)
```

### Path Patterns

Use regex patterns to include or exclude URLs:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    include_patterns=[
        r"/docs/.*",      # Only crawl /docs/
        r"/api/v\d+/.*",  # API versioned paths
    ],
    exclude_patterns=[
        r"/admin/.*",     # Skip admin pages
        r".*\.pdf$",      # Skip PDFs
    ],
)
```

### Depth Limiting

Control how deep the crawler goes from seed URLs:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    max_depth=3,  # Maximum 3 clicks from seed
)
```

## Rate Limiting

### Per-Domain Rate Limits

Respect website resources:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    requests_per_second=2.0,  # Max 2 requests/second per domain
    concurrent_requests=5,     # Max 5 concurrent requests total
)
```

### Delays

Add delays between requests:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    delay_range=(1.0, 3.0),  # Random delay 1-3 seconds
)
```

## Robots.txt Compliance

### Strict Mode (Default)

Respects all robots.txt directives:

```python
from ragcrawl.config.crawler_config import RobotsMode

config = CrawlerConfig(
    seeds=["https://example.com"],
    robots_mode=RobotsMode.STRICT,
)
```

### Off Mode

Ignores robots.txt (use responsibly):

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    robots_mode=RobotsMode.OFF,
)
```

## Page Limits

### Total Pages

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    max_pages=1000,  # Stop after 1000 pages
)
```

### Per-Domain Limits

```python
config = CrawlerConfig(
    seeds=["https://example.com", "https://other.com"],
    max_pages_per_domain=500,  # Max 500 pages per domain
)
```

## Error Handling

### Retry Configuration

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    max_retries=3,           # Retry failed requests
    retry_delay=5.0,         # Wait 5 seconds between retries
    timeout=30.0,            # 30 second timeout per request
)
```

### Circuit Breaker

The crawler automatically stops requesting from failing domains:

```python
config = CrawlerConfig(
    seeds=["https://example.com"],
    circuit_breaker_threshold=10,  # Stop after 10 consecutive failures
    circuit_breaker_reset=300,     # Reset after 5 minutes
)
```

## Hooks and Callbacks

### On Page Crawled

```python
from ragcrawl.hooks.callbacks import HookManager

def on_page(url: str, content: str, metadata: dict):
    print(f"Crawled: {url} ({len(content)} chars)")

hooks = HookManager()
hooks.on_page_crawled(on_page)

config = CrawlerConfig(
    seeds=["https://example.com"],
    hooks=hooks,
)
```

### On Error

```python
def on_error(url: str, error: Exception):
    print(f"Error crawling {url}: {error}")

hooks.on_error(on_error)
```

## Content Processing

### Redaction

Remove sensitive content before storage:

```python
from ragcrawl.hooks.callbacks import PatternRedactor

redactor = PatternRedactor([
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
])

hooks = HookManager()
hooks.add_redactor(redactor)
```

## Complete Example

```python
import asyncio
from ragcrawl.config.crawler_config import (
    CrawlerConfig,
    FetchMode,
    RobotsMode,
)
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.core.crawl_job import CrawlJob

async def crawl_documentation():
    config = CrawlerConfig(
        # Seeds
        seeds=["https://docs.example.com"],

        # Limits
        max_pages=1000,
        max_depth=10,

        # Filtering
        include_patterns=[r"/docs/.*", r"/tutorials/.*"],
        exclude_patterns=[r"/admin/.*"],

        # Fetching
        fetch_mode=FetchMode.HTTP,
        robots_mode=RobotsMode.STRICT,
        requests_per_second=2.0,
        concurrent_requests=5,
        timeout=30.0,

        # Storage
        storage=StorageConfig(
            backend=DuckDBConfig(path="./docs.duckdb")
        ),

        # Output
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./docs-output",
            include_metadata=True,
            rewrite_links=True,
        ),
    )

    job = CrawlJob(config)
    result = await job.run()

    if result.success:
        print(f"Successfully crawled {result.stats.pages_crawled} pages")
        print(f"Failed: {result.stats.pages_failed}")
        print(f"Duration: {result.duration_seconds:.1f}s")
    else:
        print(f"Crawl failed: {result.error}")

asyncio.run(crawl_documentation())
```

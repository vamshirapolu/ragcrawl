# Crawler Configuration

Complete reference for `CrawlerConfig`.

## Basic Configuration

```python
from ragcrawl.config.crawler_config import CrawlerConfig

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
    max_depth=5,
)
```

## All Options

### Seeds and Scope

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `seeds` | `list[str]` | Required | Starting URLs for crawl |
| `allowed_domains` | `list[str]` | Auto | Domains to crawl (defaults to seed domains) |
| `allow_subdomains` | `bool` | `True` | Also crawl subdomains of allowed domains |

### Limits

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_pages` | `int` | `100` | Maximum total pages to crawl |
| `max_depth` | `int` | `5` | Maximum depth from seed URLs |
| `max_pages_per_domain` | `int` | `None` | Maximum pages per domain |

### URL Filtering

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `include_patterns` | `list[str]` | `[]` | Regex patterns URLs must match |
| `exclude_patterns` | `list[str]` | `[]` | Regex patterns to skip |
| `skip_extensions` | `list[str]` | Binary | File extensions to skip |

### Fetching

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fetch_mode` | `FetchMode` | `HTTP` | HTTP, BROWSER, or HYBRID |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `user_agent` | `str` | Default | Custom user agent string |

### Rate Limiting

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `requests_per_second` | `float` | `2.0` | Max requests per second per domain |
| `concurrent_requests` | `int` | `10` | Max concurrent requests |
| `delay_range` | `tuple[float, float]` | `None` | Random delay range (min, max) |

### Robots.txt

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `robots_mode` | `RobotsMode` | `STRICT` | STRICT, OFF, or ALLOWLIST |
| `robots_allowlist` | `list[str]` | `[]` | Paths to allow despite robots.txt |

### Error Handling

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `retry_delay` | `float` | `1.0` | Delay between retries |
| `circuit_breaker_threshold` | `int` | `10` | Failures before circuit break |
| `circuit_breaker_reset` | `float` | `300.0` | Seconds before circuit reset |

### Markdown Extraction

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `markdown` | `MarkdownConfig` | Tuned defaults | Controls Crawl4AI content filtering and Markdown generator options. See [Markdown Extraction](markdown.md). |

## FetchMode Enum

```python
from ragcrawl.config.crawler_config import FetchMode

FetchMode.HTTP     # HTTP requests only (fastest)
FetchMode.BROWSER  # Headless browser (for JS sites)
FetchMode.HYBRID   # Try HTTP first, fall back to browser
```

## RobotsMode Enum

```python
from ragcrawl.config.crawler_config import RobotsMode

RobotsMode.STRICT     # Respect all robots.txt rules
RobotsMode.OFF        # Ignore robots.txt
RobotsMode.ALLOWLIST  # Respect except for allowlisted paths
```

## Complete Example

```python
from ragcrawl.config.crawler_config import (
    CrawlerConfig,
    FetchMode,
    RobotsMode,
)
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode

config = CrawlerConfig(
    # Seeds and scope
    seeds=["https://docs.example.com", "https://api.example.com"],
    allowed_domains=["docs.example.com", "api.example.com"],
    allow_subdomains=True,

    # Limits
    max_pages=1000,
    max_depth=10,
    max_pages_per_domain=500,

    # URL filtering
    include_patterns=[
        r"/docs/.*",
        r"/api/v\d+/.*",
    ],
    exclude_patterns=[
        r"/admin/.*",
        r"/internal/.*",
        r".*\.(pdf|zip|exe)$",
    ],

    # Fetching
    fetch_mode=FetchMode.HTTP,
    timeout=30.0,
    user_agent="MyBot/1.0",

    # Rate limiting
    requests_per_second=2.0,
    concurrent_requests=5,
    delay_range=(0.5, 1.5),

    # Robots
    robots_mode=RobotsMode.STRICT,

    # Error handling
    max_retries=3,
    retry_delay=2.0,
    circuit_breaker_threshold=10,

    # Storage
    storage=StorageConfig(
        backend=DuckDBConfig(path="./crawler.duckdb")
    ),

    # Output
    output=OutputConfig(
        mode=OutputMode.MULTI,
        root_dir="./output",
    ),
)
```

## Environment Variables

Some options can be set via environment variables:

```bash
export RAGCRAWL_USER_AGENT="MyBot/1.0"
export RAGCRAWL_TIMEOUT=60
export RAGCRAWL_MAX_RETRIES=5
```

# Configuration

ragcrawl is highly configurable to handle various crawling scenarios. This section covers all configuration options.

## Configuration Overview

ragcrawl uses four main configuration classes:

| Config Class | Purpose | Documentation |
|--------------|---------|---------------|
| `CrawlerConfig` | Controls crawl behavior | [Crawler Options](crawler.md) |
| `StorageConfig` | Database backend settings | [Storage Backends](storage.md) |
| `OutputConfig` | Output format and files | [Output Settings](output.md) |
| `MarkdownConfig` | Markdown extraction and filtering | [Markdown Extraction](markdown.md) |

## Quick Configuration Example

```python
from ragcrawl.config import CrawlerConfig, StorageConfig, OutputConfig
from ragcrawl.config.storage_config import DuckDBConfig

config = CrawlerConfig(
    # What to crawl
    seeds=["https://docs.example.com"],
    allowed_domains=["docs.example.com"],

    # Crawl limits
    max_pages=100,
    max_depth=5,

    # URL filtering
    include_patterns=["/docs/*", "/api/*"],
    exclude_patterns=["/blog/*", "*/print/*"],

    # Politeness
    delay_seconds=1.0,
    robots_mode="strict",

    # Storage
    storage=StorageConfig(
        backend=DuckDBConfig(path="./crawler.duckdb")
    ),

    # Output
    output=OutputConfig(
        mode="multi",
        root_dir="./output",
        include_metadata=True,
    ),
)
```

## CLI Configuration

You can also configure ragcrawl via command line:

```bash
ragcrawl crawl https://docs.example.com \
    --max-pages 100 \
    --max-depth 5 \
    --include "/docs/*" \
    --exclude "/blog/*" \
    --delay 1.0 \
    --output ./output
```

## Configuration Files

ragcrawl supports YAML configuration files:

```yaml
# ragcrawl.yaml
seeds:
  - https://docs.example.com

crawl:
  max_pages: 100
  max_depth: 5
  delay_seconds: 1.0

filters:
  include_patterns:
    - "/docs/*"
  exclude_patterns:
    - "/blog/*"

storage:
  backend: duckdb
  path: ./crawler.duckdb

output:
  mode: multi
  root_dir: ./output
```

Load with:

```bash
ragcrawl crawl --config ragcrawl.yaml
```

## Environment Variables

Some settings can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `RAGCRAWL_DB_PATH` | DuckDB database path | `./crawler.duckdb` |
| `RAGCRAWL_OUTPUT_DIR` | Default output directory | `./output` |
| `RAGCRAWL_LOG_LEVEL` | Logging level | `INFO` |
| `RAGCRAWL_USER_AGENT` | Custom user agent | `ragcrawl/0.1` |

## Configuration Sections

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } **[Crawler Options](crawler.md)**

    ---

    Configure crawl behavior, limits, URL filtering, and politeness settings.

-   :material-database:{ .lg .middle } **[Storage Backends](storage.md)**

    ---

    Choose between DuckDB and DynamoDB for data persistence.

-   :material-file-export:{ .lg .middle } **[Output Settings](output.md)**

    ---

    Configure output formats, file structure, and export options.

-   :material-format-text:{ .lg .middle } **[Markdown Extraction](markdown.md)**

    ---

    Tune Crawl4AI filters and Markdown generator options for cleaner output.

</div>

## Validation

Configuration is validated at runtime:

```python
from ragcrawl.config import CrawlerConfig
from pydantic import ValidationError

try:
    config = CrawlerConfig(
        seeds=[],  # Error: empty seeds
        max_pages=-1,  # Error: negative value
    )
except ValidationError as e:
    print(e.errors())
```

## Next Steps

- [Crawler Options](crawler.md) - Detailed crawler settings
- [Storage Backends](storage.md) - Database configuration
- [Output Settings](output.md) - Output format options

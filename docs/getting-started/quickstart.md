# Quick Start Guide

This guide will help you crawl your first website in minutes.

## Your First Crawl

### Using the CLI

The simplest way to crawl a website:

```bash
ragcrawl crawl https://docs.example.com
```

This will:
- Crawl up to 100 pages (default)
- Save to `./output` directory
- Store crawl data in `~/.ragcrawl/ragcrawl.duckdb`

### Customizing the Crawl

```bash
ragcrawl crawl https://docs.example.com \
    --max-pages 500 \
    --max-depth 10 \
    --output ./knowledge-base \
    --output-mode single \
    --export-json ./export.json \
    --verbose
```

### CLI Options Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--max-pages` | `-m` | Maximum pages to crawl |
| `--max-depth` | `-d` | Maximum crawl depth |
| `--output` | `-o` | Output directory |
| `--output-mode` | | `single` or `multi` page output |
| `--storage` | `-s` | DuckDB storage path |
| `--include` | `-i` | Include URL patterns (regex) |
| `--exclude` | `-e` | Exclude URL patterns (regex) |
| `--robots/--no-robots` | | Respect robots.txt |
| `--js/--no-js` | | Enable JavaScript rendering |
| `--export-json` | | Export to JSON file |
| `--export-jsonl` | | Export to JSONL file |
| `--verbose` | `-v` | Verbose output |

### Using the Python API

```python
import asyncio
from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.core.crawl_job import CrawlJob

async def main():
    config = CrawlerConfig(
        seeds=["https://docs.example.com"],
        max_pages=100,
        max_depth=5,
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./output",
        ),
    )

    job = CrawlJob(config)
    result = await job.run()

    if result.success:
        print(f"✓ Crawled {result.stats.pages_crawled} pages")
        print(f"✓ Duration: {result.duration_seconds:.1f}s")

        # Access documents
        for doc in result.documents[:5]:
            print(f"  - {doc.title}: {doc.url}")
    else:
        print(f"✗ Error: {result.error}")

asyncio.run(main())
```

## Output Formats

### Multi-Page Output (Default)

Each page becomes a separate Markdown file, preserving the site structure:

```
output/
├── example.com/
│   ├── index.md
│   ├── docs/
│   │   ├── getting-started.md
│   │   ├── configuration.md
│   │   └── api/
│   │       ├── overview.md
│   │       └── reference.md
│   └── blog/
│       ├── post-1.md
│       └── post-2.md
└── index.md
```

### Single-Page Output

All content combined into one file with a table of contents:

```bash
ragcrawl crawl https://docs.example.com --output-mode single
```

Output:
```
output/
└── knowledge_base.md
```

## Filtering URLs

### Include Only Specific Paths

```bash
ragcrawl crawl https://example.com \
    --include "/docs/.*" \
    --include "/api/.*"
```

### Exclude Paths

```bash
ragcrawl crawl https://example.com \
    --exclude "/admin/.*" \
    --exclude "/private/.*"
```

## Exporting Data

### JSON Export

```bash
ragcrawl crawl https://example.com --export-json ./docs.json
```

### JSONL Export (Streaming)

```bash
ragcrawl crawl https://example.com --export-jsonl ./docs.jsonl
```

## Incremental Sync

After the initial crawl, sync to get only changes:

```bash
# First, find your site ID
ragcrawl sites

# Then sync
ragcrawl sync site_abc123 --output ./updates
```

### Sync Options

| Option | Short | Description |
|--------|-------|-------------|
| `--storage` | `-s` | DuckDB storage path |
| `--max-pages` | `-m` | Maximum pages to sync |
| `--max-age` | | Only check pages older than N hours |
| `--output` | `-o` | Output directory for updates |
| `--verbose` | `-v` | Verbose output |

## Managing Crawls

### List Sites and Runs

```bash
# List all crawled sites
ragcrawl sites

# List all crawl runs
ragcrawl list

# List runs for a specific site
ragcrawl runs site_abc123

# Filter runs by status
ragcrawl list --status completed
ragcrawl list --status running
```

### Configuration Management

```bash
# Show current configuration
ragcrawl config show

# Show config file path
ragcrawl config path

# Set configuration values
ragcrawl config set storage_dir ~/.ragcrawl
ragcrawl config set user_agent "MyBot/1.0"
ragcrawl config set timeout 30

# Reset to defaults
ragcrawl config reset
```

## Common Workflows

### Documentation Site

```bash
ragcrawl crawl https://docs.myproject.com \
    --max-pages 1000 \
    --include "/docs/.*" \
    --output ./project-docs \
    --output-mode multi
```

### Blog Archive

```bash
ragcrawl crawl https://blog.example.com \
    --max-pages 500 \
    --include "/posts/.*" \
    --output-mode single \
    --export-jsonl ./blog-posts.jsonl
```

### API Documentation

```bash
ragcrawl crawl https://api.example.com/docs \
    --js \
    --max-pages 200 \
    --output ./api-docs
```

## Next Steps

- [Crawling Guide](../user-guide/crawling.md) - Advanced crawling options
- [Syncing Guide](../user-guide/syncing.md) - Keep your knowledge base updated
- [Configuration](../configuration/crawler.md) - Full configuration reference

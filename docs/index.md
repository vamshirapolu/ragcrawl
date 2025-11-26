# ragcrawl

A Python library for crawling websites and producing LLM-ready knowledge base artifacts.

## Overview

ragcrawl helps you create clean, structured knowledge bases from websites. It's designed specifically for preparing content for Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) systems.

### Key Features

- **Clean Markdown Output**: Converts web pages to clean, readable Markdown
- **Smart Crawling**: Respects robots.txt, handles rate limiting, and prevents duplicate content
- **Incremental Sync**: Efficiently update your knowledge base with only changed content
- **Multiple Output Formats**: Single-page combined output or multi-page with preserved structure
- **Chunking for RAG**: Built-in support for heading-aware and token-based chunking
- **Flexible Storage**: DuckDB (default) for local use, DynamoDB for cloud deployments
- **Export Options**: JSON and JSONL export for integration with other tools

## Quick Start

### Installation

```bash
# Basic installation (DuckDB storage, HTTP-only fetching)
pip install ragcrawl

# With browser rendering support
pip install ragcrawl[browser]

# With DynamoDB support
pip install ragcrawl[dynamodb]

# Full installation
pip install ragcrawl[all]
```

### Basic Usage

```bash
# Crawl a website
ragcrawl crawl https://docs.example.com --max-pages 100 --output ./output

# Sync for changes
ragcrawl sync site_abc123 --output ./updates

# List crawled sites
ragcrawl sites
```

### Python API

```python
import asyncio
from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.core.crawl_job import CrawlJob

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
    max_depth=5,
)

job = CrawlJob(config)
result = asyncio.run(job.run())

print(f"Crawled {result.stats.pages_crawled} pages")
for doc in result.documents:
    print(f"  - {doc.url}: {doc.title}")
```

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌───────────┐
│   Fetcher   │────▶│ Extractor│────▶│  Storage  │
│ (Crawl4AI)  │     │          │     │ (DuckDB)  │
└─────────────┘     └──────────┘     └───────────┘
       │                                    │
       ▼                                    ▼
┌─────────────┐     ┌──────────┐     ┌───────────┐
│   Frontier  │     │ Chunker  │◀────│  Export   │
│  (Priority  │     │          │     │ (JSON/L)  │
│   Queue)    │     └──────────┘     └───────────┘
└─────────────┘           │
                          ▼
                   ┌───────────┐
                   │  Output   │
                   │ Publisher │
                   └───────────┘
```

## Use Cases

### Documentation Sites
Crawl technical documentation to create a searchable knowledge base for your AI assistant.

### Content Migration
Extract content from legacy CMS systems in a structured format.

### Knowledge Management
Build internal knowledge bases from company wikis and intranets.

### Research
Collect and structure web content for research and analysis.

## Next Steps

- [Getting Started](getting-started/installation.md) - Detailed installation and setup
- [User Guide](user-guide/crawling.md) - Learn how to crawl websites
- [Configuration](configuration/crawler.md) - Customize crawler behavior
- [API Reference](api/index.md) - Full API documentation

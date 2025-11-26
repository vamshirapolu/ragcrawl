# Getting Started

Welcome to ragcrawl! This section will help you get up and running quickly.

## What is ragcrawl?

**ragcrawl** is a Python library for recursively crawling websites and producing LLM-ready knowledge base artifacts. It's designed specifically for:

- **RAG Systems**: Generate clean, structured content for Retrieval-Augmented Generation
- **Documentation Crawling**: Convert technical docs into searchable knowledge bases
- **Content Migration**: Extract and structure content from existing websites
- **Knowledge Management**: Build internal knowledge bases from company resources

## Key Features

<div class="grid cards" markdown>

-   :material-spider-web:{ .lg .middle } **Smart Crawling**

    ---

    Respects robots.txt, handles rate limiting, and prevents duplicate content with intelligent URL normalization.

-   :material-file-document:{ .lg .middle } **Clean Markdown**

    ---

    Converts web pages to clean, readable Markdown while preserving semantic structure.

-   :material-sync:{ .lg .middle } **Incremental Sync**

    ---

    Efficiently update your knowledge base with only changed content using sitemap, ETags, and content hashing.

-   :material-puzzle:{ .lg .middle } **Flexible Chunking**

    ---

    Heading-aware and token-based chunking optimized for embedding models.

</div>

## Quick Links

| Topic | Description |
|-------|-------------|
| [Installation](installation.md) | Install ragcrawl and its dependencies |
| [Quickstart](quickstart.md) | Start crawling in 5 minutes |
| [CLI Reference](../cli/index.md) | Command-line interface guide |
| [Configuration](../configuration/index.md) | Customize crawler behavior |

## System Requirements

- **Python**: 3.10 or higher
- **OS**: Linux, macOS, or Windows
- **Memory**: 512MB minimum (more for large sites)
- **Storage**: Varies based on crawled content

## Next Steps

1. **[Install ragcrawl](installation.md)** - Get the library installed
2. **[Follow the Quickstart](quickstart.md)** - Crawl your first site
3. **[Explore the User Guide](../user-guide/index.md)** - Learn advanced features

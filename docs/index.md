# ragcrawl

<p class="subtitle" style="font-size: 1.2em; color: #666; margin-top: -0.5em;">
Recursive website crawler producing LLM-ready knowledge base artifacts
</p>

---

**ragcrawl** is a Python library for crawling websites and producing clean, structured content optimized for Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) systems.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quick Start**

    ---

    Get up and running in minutes with our quickstart guide.

    [:octicons-arrow-right-24: Getting Started](getting-started/index.md)

-   :material-book-open-variant:{ .lg .middle } **User Guide**

    ---

    Learn how to crawl websites, sync updates, and export content.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   :material-cog:{ .lg .middle } **Configuration**

    ---

    Customize crawler behavior, storage, and output formats.

    [:octicons-arrow-right-24: Configuration](configuration/index.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Complete Python API documentation with examples.

    [:octicons-arrow-right-24: API Reference](api/index.md)

</div>

## Features

### Clean Markdown Output

Convert web pages to clean, readable Markdown while preserving semantic structure like headings, code blocks, and lists.

```python
from ragcrawl import CrawlJob, CrawlerConfig

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    max_pages=100,
)

job = CrawlJob(config)
result = await job.run()

for doc in result.documents:
    print(f"# {doc.title}\n{doc.markdown[:200]}...")
```

### Incremental Sync

Efficiently update your knowledge base with only changed content using sitemap detection, ETags, and content hashing.

```python
from ragcrawl import SyncJob, SyncConfig

config = SyncConfig(
    site_id="site_abc123",
    use_sitemap=True,
)

job = SyncJob(config)
result = await job.run()

print(f"New: {result.stats.pages_new}")
print(f"Updated: {result.stats.pages_changed}")
```

### RAG-Ready Chunking

Built-in chunking strategies optimized for embedding models with heading-aware and token-based options.

```python
from ragcrawl.chunking import HeadingChunker

chunker = HeadingChunker(max_tokens=500)
chunks = chunker.chunk_documents(result.documents)

for chunk in chunks:
    # Ready for embedding API
    print(f"Section: {chunk.section_path}")
    print(f"Tokens: {chunk.token_estimate}")
```

### Flexible Storage

Choose between DuckDB for local development or DynamoDB for cloud deployments.

=== "DuckDB (Local)"

    ```python
    from ragcrawl.config import StorageConfig, DuckDBConfig

    config = StorageConfig(
        backend=DuckDBConfig(path="./crawler.duckdb")
    )
    ```

=== "DynamoDB (Cloud)"

    ```python
    from ragcrawl.config import StorageConfig, DynamoDBConfig

    config = StorageConfig(
        backend=DynamoDBConfig(
            table_prefix="ragcrawl_",
            region="us-west-2",
        )
    )
    ```

## Installation

=== "pip"

    ```bash
    # Basic installation
    pip install ragcrawl

    # With browser rendering
    pip install ragcrawl[browser]

    # With DynamoDB support
    pip install ragcrawl[dynamodb]

    # Full installation
    pip install ragcrawl[all]
    ```

=== "uv"

    ```bash
    uv pip install ragcrawl
    ```

## CLI Quick Start

```bash
# Crawl a documentation site
ragcrawl crawl https://docs.example.com --max-pages 100

# Sync for updates
ragcrawl sync site_abc123

# List crawled sites
ragcrawl sites

# View crawl history
ragcrawl runs site_abc123
```

## Use Cases

| Use Case | Description |
|----------|-------------|
| **Documentation RAG** | Build Q&A systems from technical docs |
| **Knowledge Base** | Create searchable internal wikis |
| **Content Migration** | Extract structured content from websites |
| **Research** | Collect and analyze web content |

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌───────────┐
│   Fetcher   │────▶│ Extractor│────▶│  Storage  │
│ (HTTP/Browser)    │ (HTML→MD)│     │(DuckDB/Dyn)
└─────────────┘     └──────────┘     └───────────┘
       │                                    │
       ▼                                    ▼
┌─────────────┐     ┌──────────┐     ┌───────────┐
│  Frontier   │     │ Chunker  │◀────│  Export   │
│   Queue     │     │(Heading/ │     │(JSON/JSONL)
└─────────────┘     │  Token)  │     └───────────┘
                    └──────────┘
                          │
                          ▼
                    ┌───────────┐
                    │ Publisher │
                    │(Single/   │
                    │  Multi)   │
                    └───────────┘
```

## Next Steps

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **[Installation](getting-started/installation.md)**

    ---

    Detailed installation instructions

-   :material-play:{ .lg .middle } **[Quickstart](getting-started/quickstart.md)**

    ---

    Start crawling in 5 minutes

-   :material-console:{ .lg .middle } **[CLI Reference](cli/index.md)**

    ---

    Command-line interface guide

-   :material-help-circle:{ .lg .middle } **[GitHub](https://github.com/vamshirapolu/ragcrawl)**

    ---

    Report issues and contribute

</div>

## Community

We welcome contributions from the community! Here's how you can get involved:

<div class="grid cards" markdown>

-   :material-account-group:{ .lg .middle } **[Contributing](community/contributing.md)**

    ---

    Learn how to contribute code, documentation, and more

-   :material-shield-check:{ .lg .middle } **[Code of Conduct](community/code-of-conduct.md)**

    ---

    Our community standards and expectations

-   :material-lifebuoy:{ .lg .middle } **[Support](community/support.md)**

    ---

    Get help and report issues

-   :material-history:{ .lg .middle } **[Changelog](community/changelog.md)**

    ---

    Release history and updates

</div>

## License

ragcrawl is licensed under the **Apache License 2.0**. See the [LICENSE](https://github.com/vamshirapolu/ragcrawl/blob/main/LICENSE) file for details.

# API Reference

Complete API documentation for ragcrawl.

## Core Classes

### CrawlJob

The main entry point for crawling:

```python
from ragcrawl.core.crawl_job import CrawlJob

job = CrawlJob(config)
result = await job.run()
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `run()` | `CrawlResult` | Execute the crawl |
| `stop()` | `None` | Stop crawling gracefully |

### SyncJob

For incremental updates:

```python
from ragcrawl.core.sync_job import SyncJob

job = SyncJob(config)
result = await job.run()
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `run()` | `SyncResult` | Execute the sync |
| `stop()` | `None` | Stop syncing gracefully |

## Configuration Classes

### CrawlerConfig

See [Crawler Configuration](../configuration/crawler.md).

### SyncConfig

```python
from ragcrawl.config.sync_config import SyncConfig

config = SyncConfig(
    site_id="site_abc123",
    max_pages=None,
    max_age_hours=None,
    use_sitemap=True,
    use_conditional_requests=True,
)
```

### StorageConfig

See [Storage Configuration](../configuration/storage.md).

### OutputConfig

See [Output Configuration](../configuration/output.md).

## Models

### Document

```python
from ragcrawl.models.document import Document

doc = Document(
    doc_id="doc123",
    url="https://example.com/page",
    title="Page Title",
    description="Page description",
    content="# Markdown content",
    fetched_at=datetime.now(timezone.utc),
    status_code=200,
    content_type="text/html",
    language="en",
    word_count=500,
    char_count=3000,
    outlinks=["https://example.com/other"],
)
```

### Site

```python
from ragcrawl.models.site import Site

site = Site(
    site_id="site_abc123",
    name="Example Site",
    seeds=["https://example.com"],
    allowed_domains=["example.com"],
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)
```

### Page

```python
from ragcrawl.models.page import Page

page = Page(
    page_id="page123",
    site_id="site_abc123",
    url="https://example.com/page",
    first_seen=datetime.now(timezone.utc),
    last_seen=datetime.now(timezone.utc),
    depth=1,
)
```

### PageVersion

```python
from ragcrawl.models.page_version import PageVersion

version = PageVersion(
    version_id="ver123",
    page_id="page123",
    site_id="site_abc123",
    run_id="run123",
    markdown="# Content",
    content_hash="abc123",
    url="https://example.com/page",
    status_code=200,
    crawled_at=datetime.now(timezone.utc),
    created_at=datetime.now(timezone.utc),
)
```

### CrawlRun

```python
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus

run = CrawlRun(
    run_id="run123",
    site_id="site_abc123",
    status=RunStatus.RUNNING,
    created_at=datetime.now(timezone.utc),
    stats=CrawlStats(
        pages_crawled=50,
        pages_failed=2,
    ),
)
```

### Chunk

```python
from ragcrawl.models.chunk import Chunk

chunk = Chunk(
    chunk_id="chunk123",
    doc_id="doc123",
    content="Chunk content",
    chunk_index=0,
    char_count=100,
    token_count=25,
    heading_path=["Section", "Subsection"],
)
```

## Storage Backend

### StorageBackend Protocol

```python
from ragcrawl.storage.backend import StorageBackend

class StorageBackend(Protocol):
    def initialize(self) -> None: ...
    def close(self) -> None: ...

    # Sites
    def save_site(self, site: Site) -> None: ...
    def get_site(self, site_id: str) -> Optional[Site]: ...
    def list_sites(self) -> list[Site]: ...

    # Runs
    def save_crawl_run(self, run: CrawlRun) -> None: ...
    def get_crawl_run(self, run_id: str) -> Optional[CrawlRun]: ...
    def list_runs(self, site_id: str, limit: int = 10) -> list[CrawlRun]: ...

    # Pages
    def save_page(self, page: Page) -> None: ...
    def get_page(self, page_id: str) -> Optional[Page]: ...
    def get_page_by_url(self, site_id: str, url: str) -> Optional[Page]: ...
    def list_pages(self, site_id: str) -> list[Page]: ...

    # Versions
    def save_page_version(self, version: PageVersion) -> None: ...
    def get_page_version(self, version_id: str) -> Optional[PageVersion]: ...
    def get_latest_version(self, page_id: str) -> Optional[PageVersion]: ...
    def list_page_versions(self, page_id: str) -> list[PageVersion]: ...

    # Frontier
    def save_frontier_item(self, item: FrontierItem) -> None: ...
    def get_pending_frontier_items(self, run_id: str, limit: int) -> list[FrontierItem]: ...
    def frontier_url_exists(self, run_id: str, url: str) -> bool: ...
```

### Creating a Backend

```python
from ragcrawl.storage.backend import create_storage_backend
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig

config = StorageConfig(backend=DuckDBConfig(path="./db.duckdb"))
backend = create_storage_backend(config)
backend.initialize()
```

## Chunkers

### HeadingChunker

```python
from ragcrawl.chunking.heading_chunker import HeadingChunker

chunker = HeadingChunker(
    min_level=1,
    max_level=3,
    min_chunk_chars=100,
)

chunks = chunker.chunk(markdown_content)
```

### TokenChunker

```python
from ragcrawl.chunking.token_chunker import TokenChunker

chunker = TokenChunker(
    max_tokens=500,
    overlap_tokens=50,
    encoding_name="cl100k_base",
)

chunks = chunker.chunk(content)
```

## Exporters

### JSONExporter

```python
from ragcrawl.export.json_exporter import JSONExporter

exporter = JSONExporter(indent=2)
exporter.export_documents(documents, Path("output.json"))
```

### JSONLExporter

```python
from ragcrawl.export.json_exporter import JSONLExporter

exporter = JSONLExporter()
exporter.export_documents(documents, Path("output.jsonl"))
```

## Publishers

### SinglePagePublisher

```python
from ragcrawl.output.single_page import SinglePagePublisher

publisher = SinglePagePublisher(output_config)
files = publisher.publish(documents)
```

### MultiPagePublisher

```python
from ragcrawl.output.multi_page import MultiPagePublisher

publisher = MultiPagePublisher(output_config)
files = publisher.publish(documents)
```

## Utilities

### URL Normalizer

```python
from ragcrawl.filters.url_normalizer import URLNormalizer

normalizer = URLNormalizer()
normalized = normalizer.normalize(url)
domain = normalizer.extract_domain(url)
url_hash = normalizer.hash_url(url)
```

### Link Filter

```python
from ragcrawl.filters.link_filter import LinkFilter

filter = LinkFilter(
    allowed_domains=["example.com"],
    include_patterns=[r"/docs/.*"],
    exclude_patterns=[r"/admin/.*"],
)

if filter.should_follow(url):
    # Crawl the URL
    pass
```

### Hashing

```python
from ragcrawl.utils.hashing import (
    compute_doc_id,
    compute_content_hash,
    compute_url_hash,
)

doc_id = compute_doc_id(url)
content_hash = compute_content_hash(content)
url_hash = compute_url_hash(url)
```

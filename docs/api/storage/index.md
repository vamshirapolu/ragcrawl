# Storage API

ragcrawl supports pluggable storage backends for persisting crawl data.

## Overview

| Backend | Description | Use Case |
|---------|-------------|----------|
| [DuckDB](duckdb.md) | Local file-based SQL database | Default, local development |
| [DynamoDB](dynamodb.md) | AWS managed NoSQL database | Cloud deployments, scalability |

## Storage Backend Interface

All backends implement the `StorageBackend` protocol:

```python
from ragcrawl.storage import StorageBackend

class StorageBackend(Protocol):
    # Lifecycle
    def initialize(self) -> None: ...
    def close(self) -> None: ...
    def health_check(self) -> bool: ...

    # Sites
    def save_site(self, site: Site) -> None: ...
    def get_site(self, site_id: str) -> Site | None: ...
    def list_sites(self) -> list[Site]: ...

    # Crawl Runs
    def save_run(self, run: CrawlRun) -> None: ...
    def get_run(self, run_id: str) -> CrawlRun | None: ...
    def list_runs(self, site_id: str) -> list[CrawlRun]: ...

    # Pages
    def save_page(self, page: Page) -> None: ...
    def get_page(self, page_id: str) -> Page | None: ...
    def get_page_by_url(self, site_id: str, url: str) -> Page | None: ...
    def list_pages(self, site_id: str) -> list[Page]: ...

    # Versions
    def save_version(self, version: PageVersion) -> None: ...
    def get_version(self, version_id: str) -> PageVersion | None: ...
    def list_versions(self, page_id: str) -> list[PageVersion]: ...

    # Frontier
    def save_frontier_item(self, item: FrontierItem) -> None: ...
    def get_frontier_items(self, run_id: str) -> list[FrontierItem]: ...
```

## Quick Start

### Using DuckDB (Default)

```python
from ragcrawl.config.storage_config import StorageConfig, DuckDBConfig
from ragcrawl.storage import create_storage_backend

config = StorageConfig(
    backend=DuckDBConfig(path="./crawler.duckdb")
)

backend = create_storage_backend(config)
backend.initialize()

# Use the backend
sites = backend.list_sites()
```

### Using DynamoDB

```python
from ragcrawl.config.storage_config import StorageConfig, DynamoDBConfig
from ragcrawl.storage import create_storage_backend

config = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="ragcrawl_",
        region="us-west-2",
    )
)

backend = create_storage_backend(config)
backend.initialize()
```

## Factory Function

Use `create_storage_backend()` to create backends:

```python
from ragcrawl.storage import create_storage_backend

# Automatically selects backend based on config
backend = create_storage_backend(storage_config)
```

## Context Manager

Backends support context manager protocol:

```python
with create_storage_backend(config) as backend:
    backend.initialize()
    sites = backend.list_sites()
# Automatically closed
```

## Module Reference

::: ragcrawl.storage.backend
    options:
      show_root_heading: false
      members:
        - StorageBackend
        - create_storage_backend

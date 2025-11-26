# Storage Configuration

Configure where crawl data is stored.

## Overview

ragcrawl supports two storage backends:

- **DuckDB** (default): Local file-based storage, great for development and single-machine deployments
- **DynamoDB**: AWS cloud storage, suitable for distributed and serverless deployments

## DuckDB Configuration

### Basic Setup

```python
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig

storage = StorageConfig(
    backend=DuckDBConfig(path="./crawler.duckdb")
)
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `path` | `str` | `"./crawler.duckdb"` | Path to database file |
| `read_only` | `bool` | `False` | Open in read-only mode |

### CLI Usage

```bash
# Default storage
ragcrawl crawl https://example.com

# Custom storage path
ragcrawl crawl https://example.com --storage ./data/my-crawl.duckdb
```

### Multiple Databases

```python
# Separate databases for different projects
project_a = StorageConfig(backend=DuckDBConfig(path="./project-a.duckdb"))
project_b = StorageConfig(backend=DuckDBConfig(path="./project-b.duckdb"))
```

## DynamoDB Configuration

### Prerequisites

1. Install DynamoDB support:
   ```bash
   pip install ragcrawl[dynamodb]
   ```

2. Configure AWS credentials:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Basic Setup

```python
from ragcrawl.config.storage_config import DynamoDBConfig, StorageConfig

storage = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="myapp",
        region="us-east-1",
    )
)
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `table_prefix` | `str` | `"ragcrawl"` | Prefix for table names |
| `region` | `str` | `"us-east-1"` | AWS region |
| `endpoint_url` | `str` | `None` | Custom endpoint (for local testing) |
| `create_tables` | `bool` | `True` | Auto-create tables if missing |

### Table Structure

The following tables are created:

- `{prefix}-sites`: Site configurations
- `{prefix}-runs`: Crawl run records
- `{prefix}-pages`: Page metadata
- `{prefix}-versions`: Page versions with content
- `{prefix}-frontier`: Crawl queue items

### Local Development with DynamoDB Local

```python
storage = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="dev",
        region="us-east-1",
        endpoint_url="http://localhost:8000",  # DynamoDB Local
    )
)
```

Run DynamoDB Local:
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

## Fallback Configuration

Configure fallback when DynamoDB is unavailable:

```python
storage = StorageConfig(
    backend=DynamoDBConfig(
        table_prefix="prod",
        region="us-east-1",
    ),
    fallback=DuckDBConfig(path="./fallback.duckdb"),
    fail_if_unavailable=False,  # Use fallback instead of failing
)
```

## Accessing Storage Directly

```python
from ragcrawl.storage.backend import create_storage_backend
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig

# Create backend
config = StorageConfig(backend=DuckDBConfig(path="./crawler.duckdb"))
backend = create_storage_backend(config)
backend.initialize()

# Query data
sites = backend.list_sites()
for site in sites:
    print(f"Site: {site.name}")
    pages = backend.list_pages(site.site_id)
    print(f"  Pages: {len(pages)}")

# Clean up
backend.close()
```

## Data Schema

### Sites Table

| Column | Type | Description |
|--------|------|-------------|
| site_id | string | Unique identifier |
| name | string | Site name |
| seeds | json | List of seed URLs |
| allowed_domains | json | Allowed domains |
| config | json | Crawler configuration |
| created_at | datetime | Creation timestamp |
| total_pages | integer | Total pages crawled |
| total_runs | integer | Total crawl runs |

### Pages Table

| Column | Type | Description |
|--------|------|-------------|
| page_id | string | Unique identifier |
| site_id | string | Parent site |
| url | string | Page URL |
| content_hash | string | Current content hash |
| first_seen | datetime | First crawl time |
| last_crawled | datetime | Last crawl time |
| is_tombstone | boolean | Deleted page marker |

### Versions Table

| Column | Type | Description |
|--------|------|-------------|
| version_id | string | Unique identifier |
| page_id | string | Parent page |
| run_id | string | Crawl run |
| markdown | text | Markdown content |
| content_hash | string | Content hash |
| title | string | Page title |
| crawled_at | datetime | Crawl timestamp |

## Best Practices

1. **Development**: Use DuckDB for fast local iteration
2. **Production**: Use DynamoDB for scalability and durability
3. **Testing**: Use DynamoDB Local or in-memory DuckDB
4. **Backups**: DuckDB files can be copied; DynamoDB has built-in backups
5. **Migration**: Export from one backend, import to another via JSON export

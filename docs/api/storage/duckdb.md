# DuckDB Backend

The DuckDB backend provides local file-based storage using the DuckDB embedded database.

## Overview

DuckDB is the default storage backend, ideal for:

- Local development and testing
- Single-machine deployments
- Small to medium crawls (up to millions of pages)
- Fast SQL queries on crawled data

## Configuration

```python
from ragcrawl.config.storage_config import StorageConfig, DuckDBConfig

config = StorageConfig(
    backend=DuckDBConfig(
        path="./crawler.duckdb",  # Database file path
        read_only=False,          # Read-only mode
    )
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `path` | str | `"./crawler.duckdb"` | Database file path |
| `read_only` | bool | `False` | Open in read-only mode |

## Usage

### Basic Usage

```python
from ragcrawl.storage import create_storage_backend

backend = create_storage_backend(config)
backend.initialize()

# Use the backend
sites = backend.list_sites()

# Close when done
backend.close()
```

### With Context Manager

```python
with create_storage_backend(config) as backend:
    backend.initialize()
    sites = backend.list_sites()
```

### Direct SQL Queries

You can access the underlying DuckDB connection for custom queries:

```python
from ragcrawl.storage.duckdb import DuckDBBackend

backend = DuckDBBackend(duckdb_config)
backend.initialize()

# Run custom SQL
result = backend.conn.execute("""
    SELECT url, status_code, last_crawled
    FROM pages
    WHERE site_id = ?
    ORDER BY last_crawled DESC
    LIMIT 10
""", [site_id]).fetchall()
```

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `sites` | Site configurations |
| `crawl_runs` | Crawl execution records |
| `pages` | Page state and metadata |
| `page_versions` | Content version history |
| `frontier_items` | URL queue items |

### Example Queries

**Find recently changed pages:**
```sql
SELECT url, last_changed
FROM pages
WHERE site_id = 'site_abc123'
  AND last_changed > CURRENT_TIMESTAMP - INTERVAL 7 DAY
ORDER BY last_changed DESC;
```

**Get crawl statistics:**
```sql
SELECT
    COUNT(*) as total_pages,
    COUNT(CASE WHEN status_code = 200 THEN 1 END) as successful,
    COUNT(CASE WHEN is_tombstone THEN 1 END) as deleted
FROM pages
WHERE site_id = 'site_abc123';
```

**Find pages with errors:**
```sql
SELECT url, status_code, last_error
FROM pages
WHERE site_id = 'site_abc123'
  AND error_count > 0
ORDER BY error_count DESC;
```

## Performance Tips

### Indexing

The schema includes indexes for common queries. For custom queries, consider adding indexes:

```sql
CREATE INDEX idx_pages_status ON pages(site_id, status_code);
```

### Vacuuming

Periodically vacuum the database:

```python
backend.conn.execute("VACUUM")
```

### Memory Settings

For large crawls, increase memory limit:

```python
backend.conn.execute("SET memory_limit='4GB'")
```

## API Reference

::: ragcrawl.storage.duckdb.backend.DuckDBBackend
    options:
      show_root_heading: true
      members:
        - __init__
        - initialize
        - close
        - health_check

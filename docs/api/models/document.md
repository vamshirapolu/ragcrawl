# Document

The `Document` model represents crawled page content ready for output and processing.

## Overview

`Document` is the primary output model that contains:

- Cleaned markdown content
- Page metadata (title, description)
- Source information (URL, status code)
- Crawl context (run ID, site ID, timestamps)

## Usage

### Creating Documents

Documents are typically created by the crawl process, but you can create them manually:

```python
from datetime import datetime, timezone
from ragcrawl.models import Document

doc = Document(
    doc_id="abc123",
    page_id="abc123",
    source_url="https://example.com/guide",
    normalized_url="https://example.com/guide",
    markdown="# User Guide\n\nWelcome to the guide...",
    title="User Guide",
    description="Complete user guide for the product",
    status_code=200,
    content_type="text/html",
    depth=1,
    run_id="run_xyz789",
    site_id="site_abc123",
    first_seen=datetime.now(timezone.utc),
    last_seen=datetime.now(timezone.utc),
    last_crawled=datetime.now(timezone.utc),
)
```

### Accessing Content

```python
# Get the markdown content
print(doc.markdown)

# Get metadata
print(f"Title: {doc.title}")
print(f"Description: {doc.description}")
print(f"Word count: {doc.word_count}")

# Get source info
print(f"URL: {doc.source_url}")
print(f"Status: {doc.status_code}")
```

### Document Properties

```python
# Check if document is valid
if doc.status_code == 200 and not doc.is_tombstone:
    process_document(doc)

# Check content type
if doc.content_type.startswith("text/html"):
    # Process as HTML-derived content
    pass
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | str | Unique document identifier |
| `page_id` | str | Associated page ID |
| `source_url` | str | Original URL |
| `normalized_url` | str | Normalized URL for deduplication |
| `markdown` | str | Cleaned markdown content |
| `title` | str | Page title |
| `description` | str | Page description/meta |
| `status_code` | int | HTTP status code |
| `content_type` | str | Content MIME type |
| `language` | str | Detected language |
| `depth` | int | Crawl depth from seed |
| `word_count` | int | Word count |
| `char_count` | int | Character count |
| `outlinks` | list[str] | Outbound links |
| `run_id` | str | Crawl run ID |
| `site_id` | str | Site ID |
| `first_seen` | datetime | First crawl time |
| `last_seen` | datetime | Last seen time |
| `last_crawled` | datetime | Last crawl time |
| `is_tombstone` | bool | Deleted page marker |

## API Reference

::: ragcrawl.models.document.Document
    options:
      show_root_heading: true
      members:
        - doc_id
        - page_id
        - source_url
        - normalized_url
        - markdown
        - title
        - description
        - status_code
        - content_type

# Exporting Guide

Export crawled content in various formats.

## Export Formats

### JSON Export

Export all documents to a single JSON file:

```python
from ragcrawl.export.json_exporter import JSONExporter
from pathlib import Path

exporter = JSONExporter(indent=2)
exporter.export_documents(documents, Path("./docs.json"))
```

Output format:
```json
[
  {
    "doc_id": "abc123",
    "url": "https://example.com/page1",
    "title": "Page 1",
    "content": "# Page 1\n\nContent here...",
    "fetched_at": "2024-01-15T10:30:00Z",
    "status_code": 200,
    "word_count": 500
  },
  {
    "doc_id": "def456",
    "url": "https://example.com/page2",
    "title": "Page 2",
    "content": "# Page 2\n\nMore content...",
    "fetched_at": "2024-01-15T10:31:00Z",
    "status_code": 200,
    "word_count": 300
  }
]
```

### JSONL Export (Streaming)

Export one document per line for streaming/large datasets:

```python
from ragcrawl.export.json_exporter import JSONLExporter
from pathlib import Path

exporter = JSONLExporter()
exporter.export_documents(documents, Path("./docs.jsonl"))
```

Output format:
```
{"doc_id":"abc123","url":"https://example.com/page1","title":"Page 1",...}
{"doc_id":"def456","url":"https://example.com/page2","title":"Page 2",...}
```

## CLI Export

### During Crawl

```bash
# Export to JSON
ragcrawl crawl https://example.com --export-json ./docs.json

# Export to JSONL
ragcrawl crawl https://example.com --export-jsonl ./docs.jsonl

# Both formats
ragcrawl crawl https://example.com \
    --export-json ./docs.json \
    --export-jsonl ./docs.jsonl
```

### From Storage

Export previously crawled content:

```python
from ragcrawl.storage.backend import create_storage_backend
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.export.json_exporter import JSONExporter
from ragcrawl.models.document import Document

# Connect to storage
config = StorageConfig(backend=DuckDBConfig(path="./crawler.duckdb"))
backend = create_storage_backend(config)
backend.initialize()

# Get site
site = backend.list_sites()[0]

# Get all pages with latest versions
documents = []
pages = backend.list_pages(site.site_id)

for page in pages:
    if page.is_tombstone:
        continue

    version = backend.get_latest_version(page.page_id)
    if version:
        doc = Document(
            doc_id=page.page_id,
            url=page.url,
            title=version.title,
            content=version.markdown,
            fetched_at=version.crawled_at,
            status_code=version.status_code,
            content_type=version.content_type,
            word_count=version.word_count,
        )
        documents.append(doc)

# Export
exporter = JSONExporter()
exporter.export_documents(documents, Path("./export.json"))

backend.close()
```

## Custom Export Fields

### Select Specific Fields

```python
import json
from pathlib import Path

def export_minimal(documents, output_path):
    """Export only essential fields."""
    data = [
        {
            "url": doc.url,
            "title": doc.title,
            "content": doc.content,
        }
        for doc in documents
    ]

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
```

### Add Custom Fields

```python
def export_with_metadata(documents, output_path, site_name):
    """Export with additional metadata."""
    data = [
        {
            "id": doc.doc_id,
            "source": site_name,
            "url": doc.url,
            "title": doc.title,
            "content": doc.content,
            "crawled_at": doc.fetched_at.isoformat(),
            "word_count": doc.word_count,
            "char_count": doc.char_count,
        }
        for doc in documents
    ]

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
```

## Export for RAG Systems

### OpenAI/LangChain Format

```python
def export_for_langchain(documents, output_path):
    """Export in LangChain Document format."""
    data = [
        {
            "page_content": doc.content,
            "metadata": {
                "source": doc.url,
                "title": doc.title,
                "language": doc.language,
            },
        }
        for doc in documents
    ]

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
```

### Vector Database Format

```python
def export_for_pinecone(documents, chunks):
    """Export chunks with embeddings format."""
    records = []

    for chunk in chunks:
        doc = next(d for d in documents if d.doc_id == chunk.doc_id)
        records.append({
            "id": chunk.chunk_id,
            "text": chunk.content,
            "metadata": {
                "doc_id": chunk.doc_id,
                "url": doc.url,
                "title": doc.title,
                "heading": " > ".join(chunk.heading_path or []),
                "chunk_index": chunk.chunk_index,
            },
        })

    return records
```

## Incremental Export

### Export Changes Only

```python
from ragcrawl.export.events import EventEmitter

emitter = EventEmitter()
changed_docs = []

@emitter.on("page_changed")
def collect_change(event):
    changed_docs.append(event.document)

# After sync completes
if changed_docs:
    exporter = JSONExporter()
    exporter.export_documents(changed_docs, Path("./changes.json"))
```

### Append to JSONL

```python
def append_to_jsonl(documents, output_path):
    """Append new documents to existing JSONL file."""
    import json

    with open(output_path, "a") as f:
        for doc in documents:
            line = json.dumps(doc.model_dump(), default=str)
            f.write(line + "\n")
```

## Compression

### Gzip Export

```python
import gzip
import json

def export_gzipped(documents, output_path):
    """Export as gzipped JSON."""
    data = [doc.model_dump() for doc in documents]

    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, default=str)
```

### Read Gzipped

```python
import gzip
import json

with gzip.open("docs.json.gz", "rt") as f:
    documents = json.load(f)
```

## Best Practices

1. **Use JSONL for large datasets**: Better for streaming and memory efficiency
2. **Include source URLs**: Essential for citation and verification
3. **Add timestamps**: Track when content was crawled
4. **Compress large exports**: Save disk space and transfer time
5. **Export incrementally**: Only export changes for efficiency

# Export API

ragcrawl provides exporters and publishers for outputting crawled content.

## Overview

### Exporters

Export data to structured formats:

| Exporter | Format | Description |
|----------|--------|-------------|
| `JSONExporter` | .json | Single JSON array |
| `JSONLExporter` | .jsonl | JSON Lines format |

### Publishers

Output markdown files:

| Publisher | Output | Description |
|-----------|--------|-------------|
| `SinglePagePublisher` | One file | Combined markdown |
| `MultiPagePublisher` | Directory | Preserves structure |

## JSONExporter

Export documents to a single JSON file.

```python
from ragcrawl.export import JSONExporter
from pathlib import Path

exporter = JSONExporter(indent=2)

# Export documents
exporter.export_documents(documents, Path("output.json"))

# Export chunks
exporter.export_chunks(chunks, Path("chunks.json"))
```

### Output Format

```json
[
  {
    "doc_id": "abc123",
    "source_url": "https://example.com/page",
    "title": "Page Title",
    "markdown": "# Page Title\n\nContent...",
    "status_code": 200,
    "word_count": 500
  }
]
```

## JSONLExporter

Export documents to JSON Lines format (one JSON object per line).

```python
from ragcrawl.export import JSONLExporter
from pathlib import Path

exporter = JSONLExporter()

# Export documents
exporter.export_documents(documents, Path("output.jsonl"))
```

### Output Format

```jsonl
{"doc_id":"abc123","source_url":"https://example.com/page1",...}
{"doc_id":"def456","source_url":"https://example.com/page2",...}
```

## SinglePagePublisher

Combine all documents into a single markdown file.

```python
from ragcrawl.output import SinglePagePublisher
from ragcrawl.config import OutputConfig, OutputMode

config = OutputConfig(
    mode=OutputMode.SINGLE,
    root_dir="./output",
    single_file_name="knowledge_base.md",
    include_toc=True,
    include_metadata=True,
)

publisher = SinglePagePublisher(config)
files = publisher.publish(documents)

print(f"Created: {files[0]}")
```

### Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `single_file_name` | str | "output.md" | Output filename |
| `include_toc` | bool | True | Add table of contents |
| `include_metadata` | bool | True | Add source URLs |

## MultiPagePublisher

Output documents preserving URL structure.

```python
from ragcrawl.output import MultiPagePublisher
from ragcrawl.config import OutputConfig, OutputMode

config = OutputConfig(
    mode=OutputMode.MULTI,
    root_dir="./output",
    rewrite_links=True,
    generate_index=True,
    include_metadata=True,
)

publisher = MultiPagePublisher(config)
files = publisher.publish(documents)

print(f"Created {len(files)} files")
```

### Output Structure

```
output/
├── index.md
├── example.com/
│   ├── docs/
│   │   ├── getting-started.md
│   │   └── api-reference.md
│   └── blog/
│       └── post-1.md
```

### Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `root_dir` | str | "./output" | Output directory |
| `rewrite_links` | bool | True | Rewrite internal links |
| `generate_index` | bool | True | Create index file |
| `include_metadata` | bool | True | Add frontmatter |

## Output Configuration

```python
from ragcrawl.config import OutputConfig, OutputMode

config = OutputConfig(
    mode=OutputMode.MULTI,  # or SINGLE
    root_dir="./output",

    # Single-page options
    single_file_name="combined.md",
    include_toc=True,

    # Multi-page options
    rewrite_links=True,
    generate_index=True,

    # Common options
    include_metadata=True,
)
```

## Module Reference

::: ragcrawl.export
    options:
      show_root_heading: false
      members:
        - JSONExporter
        - JSONLExporter

::: ragcrawl.output
    options:
      show_root_heading: false
      members:
        - SinglePagePublisher
        - MultiPagePublisher

# Output Configuration

Configure how crawled content is published.

## Overview

ragcrawl can output content in two modes:

- **Multi-page**: Each page becomes a separate Markdown file
- **Single-page**: All content combined into one file

## OutputConfig

```python
from ragcrawl.config.output_config import OutputConfig, OutputMode

config = OutputConfig(
    mode=OutputMode.MULTI,
    root_dir="./output",
)
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mode` | `OutputMode` | `MULTI` | SINGLE or MULTI |
| `root_dir` | `str` | `"./output"` | Output directory |
| `include_metadata` | `bool` | `True` | Include source URLs in output |
| `include_toc` | `bool` | `True` | Include table of contents (SINGLE mode) |
| `rewrite_links` | `bool` | `True` | Rewrite internal links (MULTI mode) |
| `single_file_name` | `str` | `"knowledge_base.md"` | Output filename (SINGLE mode) |
| `generate_index` | `bool` | `True` | Generate index.md (MULTI mode) |

## Multi-Page Output

Each crawled page becomes a separate Markdown file:

```python
config = OutputConfig(
    mode=OutputMode.MULTI,
    root_dir="./docs-output",
    include_metadata=True,
    rewrite_links=True,
    generate_index=True,
)
```

### Output Structure

```
docs-output/
├── index.md                 # Generated index
├── example.com/
│   ├── index.md
│   ├── docs/
│   │   ├── getting-started.md
│   │   ├── installation.md
│   │   └── api/
│   │       ├── overview.md
│   │       └── reference.md
│   └── blog/
│       ├── post-1.md
│       └── post-2.md
```

### Link Rewriting

Internal links are automatically converted:

**Original HTML:**
```html
<a href="/docs/api/overview">API Overview</a>
```

**Output Markdown:**
```markdown
[API Overview](./api/overview.md)
```

### Metadata Headers

Each file includes source information:

```markdown
<!-- Source: https://example.com/docs/getting-started -->
<!-- Crawled: 2024-01-15T10:30:00Z -->

# Getting Started

Content here...
```

## Single-Page Output

All content combined into one file:

```python
config = OutputConfig(
    mode=OutputMode.SINGLE,
    root_dir="./output",
    single_file_name="knowledge_base.md",
    include_toc=True,
    include_metadata=True,
)
```

### Output Structure

```
output/
└── knowledge_base.md
```

### File Format

```markdown
# Knowledge Base

Generated from https://docs.example.com

## Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)

---

## Getting Started

<!-- Source: https://example.com/docs/getting-started -->

Content here...

---

## Installation

<!-- Source: https://example.com/docs/installation -->

Content here...
```

## Custom Publishers

Create custom output formats:

```python
from ragcrawl.output.publisher import MarkdownPublisher
from ragcrawl.config.output_config import OutputConfig
from pathlib import Path

class MyCustomPublisher(MarkdownPublisher):
    def publish(self, documents: list) -> list[Path]:
        output_files = []

        for doc in documents:
            # Custom processing
            content = self.format_document(doc)

            # Custom filename
            filename = f"{doc.doc_id}.md"
            path = Path(self.config.root_dir) / filename

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            output_files.append(path)

        return output_files

    def format_document(self, doc):
        return f"""---
title: {doc.title}
url: {doc.url}
date: {doc.fetched_at.isoformat()}
---

{doc.content}
"""
```

## CLI Options

```bash
# Multi-page output (default)
ragcrawl crawl https://example.com --output ./output --output-mode multi

# Single-page output
ragcrawl crawl https://example.com --output ./output --output-mode single
```

## Best Practices

1. **Multi-page for large sites**: Easier to navigate and search
2. **Single-page for LLM context**: One file for full-text RAG
3. **Enable link rewriting**: Keeps navigation working offline
4. **Include metadata**: Helps trace content back to sources
5. **Use consistent structure**: Match the site's URL hierarchy

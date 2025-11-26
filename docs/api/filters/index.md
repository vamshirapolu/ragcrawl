# Filters API

ragcrawl provides URL filtering utilities to control which pages are crawled.

## Overview

| Filter | Description |
|--------|-------------|
| `LinkFilter` | Complete URL filtering with domains, patterns, and deduplication |
| `PatternMatcher` | Glob/regex pattern matching |
| `URLNormalizer` | URL normalization and hashing |
| `ExtensionFilter` | File extension filtering |

## LinkFilter

The main filter class combining all filtering logic.

```python
from ragcrawl.filters import LinkFilter, FilterReason

link_filter = LinkFilter(
    allowed_domains=["docs.example.com"],
    allow_subdomains=True,
    include_patterns=["/docs/*", "/api/*"],
    exclude_patterns=["/admin/*", "*secret*"],
    blocked_extensions=[".pdf", ".zip", ".png"],
)

# Check if URL should be crawled
result = link_filter.filter("https://docs.example.com/api/users")

if result.allowed:
    crawl_url(url)
else:
    print(f"Filtered: {result.reason}")
    # FilterReason.DOMAIN_NOT_ALLOWED
    # FilterReason.EXCLUDED_PATTERN
    # FilterReason.NO_INCLUDE_MATCH
    # FilterReason.BLOCKED_EXTENSION
    # FilterReason.ALREADY_SEEN
```

### Deduplication

```python
# Track seen URLs
link_filter.mark_seen("https://example.com/page1")

# Check with deduplication
result = link_filter.filter("https://example.com/page1", check_seen=True)
if not result.allowed:
    print(f"Already seen: {result.reason == FilterReason.ALREADY_SEEN}")
```

### Configuration

| Option | Type | Description |
|--------|------|-------------|
| `allowed_domains` | list[str] | Domains to allow |
| `allow_subdomains` | bool | Include subdomains |
| `include_patterns` | list[str] | URL patterns to include |
| `exclude_patterns` | list[str] | URL patterns to exclude |
| `blocked_extensions` | list[str] | File extensions to skip |

## PatternMatcher

Match URLs against glob or regex patterns.

```python
from ragcrawl.filters import PatternMatcher

matcher = PatternMatcher(
    include_patterns=["/docs/*", "/api/v1/*"],
    exclude_patterns=["*internal*", "*private*"],
    case_sensitive=False,
)

# Check if URL path should be included
if matcher.should_include("/docs/getting-started"):
    print("URL matches include pattern")

if not matcher.should_include("/admin/settings"):
    print("URL doesn't match any include pattern")
```

### Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `/docs/*` | `/docs/anything` |
| `**/api/*` | `any/path/api/anything` |
| `*.pdf` | Files ending in .pdf |
| `/api/v[12]/*` | `/api/v1/` or `/api/v2/` |

Patterns support both glob syntax (`*`, `**`, `?`) and regex (when containing `|`, `^`, `$`, etc.).

## URLNormalizer

Normalize URLs for consistent comparison and hashing.

```python
from ragcrawl.filters import URLNormalizer

normalizer = URLNormalizer(
    remove_fragments=True,
    remove_tracking_params=True,
    sort_query_params=True,
)

# Normalize URL
normalized = normalizer.normalize(
    "HTTPS://Example.COM/Page?utm_source=google&id=1#section"
)
# Result: "https://example.com/page?id=1"

# Get domain
domain = normalizer.get_domain("https://docs.example.com/page")
# Result: "docs.example.com"

# Get registered domain
base = normalizer.get_registered_domain("https://docs.example.com/page")
# Result: "example.com"

# Check same domain
same = normalizer.is_same_domain(
    "https://docs.example.com",
    "https://api.example.com",
    include_subdomains=True,
)
# Result: True
```

### Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `remove_fragments` | bool | True | Remove URL fragments (#) |
| `remove_tracking_params` | bool | True | Remove UTM params etc. |
| `sort_query_params` | bool | True | Sort query parameters |
| `lowercase_path` | bool | False | Lowercase URL path |

## ExtensionFilter

Filter URLs by file extension.

```python
from ragcrawl.filters import ExtensionFilter

ext_filter = ExtensionFilter(
    blocked_extensions=[".pdf", ".png", ".jpg", ".zip", ".exe"]
)

# Check if URL is blocked
if ext_filter.is_blocked("https://example.com/report.pdf"):
    print("PDF files are blocked")

# Get extension
ext = ext_filter.get_extension("https://example.com/file.tar.gz")
# Result: ".gz"
```

## Integration Example

```python
from ragcrawl.filters import LinkFilter

# Create comprehensive filter
link_filter = LinkFilter(
    allowed_domains=["docs.python.org"],
    allow_subdomains=False,
    include_patterns=[
        "/3/*",          # Python 3 docs only
    ],
    exclude_patterns=[
        "*/whatsnew/*",  # Skip what's new pages
        "*/_sources/*",  # Skip source files
    ],
    blocked_extensions=[
        ".pdf", ".zip", ".tar.gz",
        ".png", ".jpg", ".gif", ".svg",
    ],
)

# Use in crawling
for url in discovered_urls:
    result = link_filter.filter(url, check_seen=True)
    if result.allowed:
        link_filter.mark_seen(url)
        queue.add(url)
```

## Module Reference

::: ragcrawl.filters
    options:
      show_root_heading: false
      members:
        - LinkFilter
        - PatternMatcher
        - URLNormalizer
        - ExtensionFilter

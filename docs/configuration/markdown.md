# Markdown Extraction Settings

`MarkdownConfig` controls how Crawl4AI extracts and filters Markdown for LLM-ready output. It is used by both `CrawlerConfig` and `SyncConfig` and tuned for documentation-style sites by default.

## Quick Example

```python
from ragcrawl.config import CrawlerConfig
from ragcrawl.config.markdown_config import MarkdownConfig, ContentFilterType

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    markdown=MarkdownConfig(
        content_filter=ContentFilterType.PRUNING,
        pruning_threshold=0.55,
        excluded_tags=["nav", "footer", "form"],
        ignore_images=True,
        include_citations=True,
    ),
)
```

> Tip: `content_filter="bm25"` requires `user_query`; otherwise ragcrawl falls back to no filter and logs a warning.

## CLI Usage

You can pass a TOML/JSON file with Markdown settings to the CLI:

```toml
# markdown.config.toml
content_filter = "pruning"
pruning_threshold = 0.55
ignore_images = true
include_citations = true
excluded_tags = ["nav", "footer", "form"]
```

```bash
ragcrawl crawl https://docs.example.com --markdown-config ./markdown.config.toml
```

JSON works too:

```json
{
  "content_filter": "bm25",
  "user_query": "authentication guide",
  "bm25_threshold": 1.2
}
```

## Content Filters

| Option | Type / Values | Default | Description |
|--------|---------------|---------|-------------|
| `content_filter` | `none \| pruning \| bm25` | `pruning` | Select the Crawl4AI content filter. |
| `word_count_threshold` | `int` | `15` | Minimum words per text block to keep. |
| `remove_overlay_elements` | `bool` | `true` | Drop popups and modals. |
| `process_iframes` | `bool` | `true` | Include iframe content. |
| `remove_forms` | `bool` | `true` | Strip form elements from output. |

### Pruning Filter (default)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `pruning_threshold` | `float` | `0.55` | Higher = more aggressive boilerplate removal. |
| `pruning_threshold_type` | `str` | `"fixed"` | `"fixed"` or `"dynamic"` scoring strategy. |
| `pruning_min_word_threshold` | `int` | `15` | Minimum words per block to keep. |

### BM25 Filter (query-focused)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `bm25_threshold` | `float` | `1.0` | Relevance cutoff; higher is stricter. |
| `user_query` | `str \| None` | `None` | Required when `content_filter="bm25"`. |

## HTML Selection

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `excluded_tags` | `list[str]` | `["nav","footer","header","aside","noscript"]` | Tags to drop entirely. |
| `excluded_selector` | `str \| None` | `None` | CSS selector to exclude (e.g., `.sidebar, .ads`). |
| `css_selector` | `str \| None` | `None` | CSS selector to target (e.g., `article, main`). |
| `target_elements` | `list[str] \| None` | `None` | Flexible element targets for extraction. |

## Link Filtering

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `exclude_external_links` | `bool` | `false` | Drop hyperlinks to other domains. |
| `exclude_social_media_links` | `bool` | `true` | Remove common social links. |
| `exclude_external_images` | `bool` | `false` | Remove images hosted off-domain. |
| `exclude_domains` | `list[str]` | `[]` | Specific domains to strip from links. |

## Markdown Generator Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ignore_links` | `bool` | `false` | Remove all links from Markdown. |
| `ignore_images` | `bool` | `false` | Remove all images from Markdown. |
| `escape_html` | `bool` | `true` | Convert HTML entities to text. |
| `body_width` | `int` | `0` | Wrap text at width; `0` = no wrapping. |
| `skip_internal_links` | `bool` | `false` | Drop same-page anchor links. |
| `include_sup_sub` | `bool` | `true` | Preserve sup/sub formatting. |

## Output Selection

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_fit_markdown` | `bool` | `true` | Prefer filtered `fit_markdown` when available, otherwise `raw_markdown`. |
| `include_citations` | `bool` | `false` | Use `markdown_with_citations` (reference-style links) when present. |

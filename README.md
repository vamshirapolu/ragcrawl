# RAGcrawl: Scalable Site Crawler for RAG Pipelines

Recursive website crawler producing LLM-ready knowledge base artifacts.

A standalone Python library to **recursively crawl websites** and produce **LLM-ready knowledge base artifacts** (clean Markdown + rich metadata + chunking), with **incremental sync** (detect page updates efficiently) and **pluggable storage** (DuckDB by default, optional DynamoDB via PynamoDB). Designed to feel like “Scrapy-grade control” with “LLM-grade output”.

---

## Key Capabilities

### Crawling (Recursive + Pattern-Based)
- Crawl from one or more **seed URLs** and discover/enqueue links recursively.
- **Include/exclude patterns** (regex/glob), plus boundary constraints:
  - allowed domains/subdomains
  - allowed schemes (http/https)
  - allowed path prefixes
  - denylists for extensions (e.g., `.zip`, `.png`) and query params
- Deterministic **URL normalization & deduplication**:
  - ignore fragments (`#...`)
  - normalize trailing slashes
  - canonical URL handling (where applicable)
- Crawl limits:
  - max depth, max pages
  - max concurrency (global + per-domain)

### Politeness / Compliance / Reliability
- Robots mode: `strict | off | allowlist`
- User-agent control, per-domain rate limits, delays, concurrency caps
- Retries with exponential backoff + per-domain circuit breaker
- Redirect handling, timeouts, error taxonomy + partial success behavior
- Support for cookies/sessions, custom headers, auth flows, proxies

### Fetching & Rendering Modes
- **HTTP mode** (fast)
- **Browser/JS rendering** mode (dynamic pages)
- **Hybrid** mode (try HTTP, fallback to browser if content incomplete)

### LLM-Ready Extraction
- Clean **Markdown output**:
  - preserves structure (headings, lists, code blocks)
  - removes scripts/styles/boilerplate
  - optional link references
- Optional retention of:
  - cleaned HTML
  - plain text
  - extracted structured JSON (if configured)

### KB / RAG Extras (First-Class)
- **Stable IDs**:
  - `doc_id/page_id = hash(normalized_url)`
- **Versioning**:
  - `version_id = content_hash` and/or crawl timestamp
  - store `PageVersion` rows per detected change
- **Rich metadata** per page:
  - source + canonical URL, title, content-type/status
  - depth, referrer, run id
  - timestamps: first_seen / last_seen / last_crawled / last_changed
  - headings outline, section path (when available)
  - diagnostics (latency, extraction stats, errors)
- **Tombstones** for deletions (404/410), enabling KB removals downstream
- **Quality gates**:
  - min text length
  - thin/duplicate content thresholds
  - blocklist patterns (e.g., tag/search pages)
  - optional language detection
- Optional **redaction hook** before persistence for sensitive/PII handling

### Chunking & Export
- Built-in chunkers:
  - heading-aware Markdown chunking
  - token/size-based chunking (model-agnostic)
- Chunk metadata:
  - `chunk_id`, `doc_id`, section path, offsets, token estimates
- Exporters:
  - JSON / JSONL artifacts for downstream embedding/vector pipelines
  - change events: `page_changed`, `page_deleted` (tombstone) for index updates

### Output Markdown Publishing Formats (User-Configurable)
Users can choose how Markdown is written to disk:
1. **Single-page Markdown**
   - Concatenate crawled pages into one Markdown file
   - Auto-generate Table of Contents (TOC)
   - Page sections are anchor-linked for navigation
2. **Multi-page Markdown (preserve site folder structure)**
   - One `.md` per crawled URL
   - Output path mirrors site path under an output root  
     Example: `/docs/a/b` → `out/docs/a/b.md`
   - Rewrite internal links to local markdown equivalents
   - Optional navigation extras:
     - index/TOC pages
     - breadcrumbs headers
     - previous/next links
   - Stable output paths across syncs; configurable handling for deletions:
     - tombstone pages or redirect stubs

### Markdown Extraction Controls
- Switch content filters: none, pruning (default), or BM25 (requires `user_query`).
- Defaults tuned for docs: pruning filter, threshold `0.55`, min words per block `15`, and global text threshold `15`.
- Tune boilerplate removal: thresholds, min words, tag/selector exclusions, iframe/form stripping.
- Link hygiene: drop external/social links or specific domains; optionally remove all links/images.
- Output selection: prefer `fit_markdown`, fall back to `raw_markdown`, or emit citations when available.

```python
from ragcrawl.config import CrawlerConfig
from ragcrawl.config.markdown_config import MarkdownConfig, ContentFilterType

config = CrawlerConfig(
    seeds=["https://docs.example.com"],
    markdown=MarkdownConfig(
        content_filter=ContentFilterType.PRUNING,
        excluded_tags=["nav", "footer"],
        ignore_images=True,
        include_citations=True,
    ),
)
```

CLI: save the same fields in `markdown.config.toml` or JSON and pass `--markdown-config ./markdown.config.toml` to `ragcrawl crawl`.

---

## Storage Backends (Pluggable)

### Default: DuckDB (No Config Needed)
- Works out of the box.
- Stores crawl state and content locally (file-backed DuckDB).

### Optional: DynamoDB (Explicitly Enabled)
- Enabled only when the user configures it.
- Uses **PynamoDB** as the ORM.
- Recommended for shared/remote persistence and multi-environment workflows.

### Backend Parity (Minimum Entities)
Both backends must support the same conceptual entities and APIs:
- `Site` (config snapshot)
- `CrawlRun` (status/stats)
- `Page` (freshness fields + current version pointer)
- `PageVersion` (stored content + metadata + outlinks)
- Optional `FrontierItem` (pause/resume, progress tracking)

### Configuration Behavior
- If DynamoDB is **missing/misconfigured**, default behavior is:
  - fall back to DuckDB and log a clear warning
- Strict mode supported:
  - `fail_if_unavailable=True` stops execution instead of falling back silently

---

## Sync / Incremental Crawl (Detect Updates)

The library supports efficient syncing by combining multiple signals:

1. **Conditional HTTP Revalidation (Preferred)**
   - Store `ETag` and/or `Last-Modified` per page
   - Re-crawl with:
     - `If-None-Match` / `If-Modified-Since`
   - Honor **304 Not Modified** and skip parsing/persistence work

2. **Sitemap-Driven Prioritization (Optional)**
   - Parse `sitemap.xml` / sitemap index
   - Use `<lastmod>` to prioritize/limit recrawls

3. **Content Hash Diffing (Fallback)**
   - `content_hash = sha256(normalized_markdown)`
   - If changed → create new `PageVersion` + emit change event
   - Includes noise-reduction guidance to minimize false positives

Recommended default sync strategy: **Sitemap (if present) → Conditional GET → Hash diff fallback**.

---

## Installation

### From PyPI (pip)
```bash
pip install ragcrawl
```

From PyPI (uv)
```bash
uv pip install ragcrawl
```
or

```bash
uv add ragcrawl
```

Optional Dependencies (Extras)
```bash
# DynamoDB backend (PynamoDB + AWS deps)
pip install "ragcrawl[dynamodb]"
````

```bash
# Browser/JS rendering support
pip install "ragcrawl[browser]"
```

```bash
# Everything
pip install "ragcrawl[all]"
```

Note: DuckDB is the default backend. Depending on packaging choices, DuckDB may be included in base dependencies to guarantee "works by default".

---

## CLI Reference

ragcrawl provides a full-featured command-line interface for crawling and managing sites.

### Available Commands


```
ragcrawl --help          # Show all commands
ragcrawl --version       # Show version
```

| Command | Description |
|---------|-------------|
| `crawl` | Crawl websites from seed URLs |
| `sync` | Sync a previously crawled site for changes |
| `sites` | List all crawled sites |
| `runs` | List crawl runs for a specific site |
| `list` | List all crawl runs (with filters) |
| `config` | Manage ragcrawl configuration |

### crawl

Crawl websites from one or more seed URLs:

```bash
ragcrawl crawl https://docs.example.com

# With options
ragcrawl crawl https://docs.example.com \
    --max-pages 500 \
    --max-depth 10 \
    --output ./knowledge-base \
    --output-mode multi \
    --include "/docs/.*" \
    --exclude "/admin/.*" \
    --robots \
    --export-json ./docs.json \
    --verbose
```

**Options:**
- `-m, --max-pages INTEGER` - Maximum pages to crawl
- `-d, --max-depth INTEGER` - Maximum crawl depth
- `-o, --output TEXT` - Output directory
- `--output-mode [single|multi]` - Output mode (single file or multi-page)
- `-s, --storage PATH` - DuckDB storage path (default: `~/.ragcrawl/ragcrawl.duckdb`)
- `-i, --include TEXT` - Include URL patterns (regex, repeatable)
- `-e, --exclude TEXT` - Exclude URL patterns (regex, repeatable)
- `--robots / --no-robots` - Respect robots.txt
- `--js / --no-js` - Enable JavaScript rendering
- `--export-json PATH` - Export documents to JSON file
- `--export-jsonl PATH` - Export documents to JSONL file
- `-v, --verbose` - Verbose output

### sync

Sync a previously crawled site to detect changes:

```bash
# First, find your site ID
ragcrawl sites

# Then sync
ragcrawl sync site_abc123

# With options
ragcrawl sync site_abc123 \
    --max-pages 500 \
    --max-age 24 \
    --output ./updates \
    --verbose
```

**Options:**
- `-s, --storage PATH` - DuckDB storage path
- `-m, --max-pages INTEGER` - Maximum pages to sync
- `--max-age FLOAT` - Only check pages older than N hours
- `-o, --output TEXT` - Output directory for updates
- `-v, --verbose` - Verbose output

### sites

List all crawled sites:

```bash
ragcrawl sites
ragcrawl sites --storage ./my-crawler.duckdb
```

### runs

List crawl runs for a specific site:

```bash
ragcrawl runs site_abc123
ragcrawl runs site_abc123 --limit 10
```

### list

List all crawl runs with optional filters:

```bash
ragcrawl list
ragcrawl list --limit 20
ragcrawl list --site site_abc123
ragcrawl list --status completed
ragcrawl list --status running
```

**Options:**
- `-s, --storage PATH` - DuckDB storage path
- `-l, --limit INTEGER` - Maximum number of runs to show
- `--site TEXT` - Filter by site ID
- `--status [running|completed|partial|failed]` - Filter by status

### config

Manage ragcrawl configuration:

```bash
# Show current configuration
ragcrawl config show

# Show config file path
ragcrawl config path

# Set a configuration value
ragcrawl config set storage_dir ~/.ragcrawl
ragcrawl config set user_agent "MyBot/1.0"
ragcrawl config set timeout 30

# Reset to defaults
ragcrawl config reset
ragcrawl config reset --yes  # Skip confirmation
```

---

## Quickstart (DuckDB Default)

```python
from ragcrawl import CrawlJob, CrawlerConfig

config = CrawlerConfig(
    seeds=["https://example.com/docs"],
    include_patterns=[r"/docs/.*"],
    exclude_patterns=[r"/docs/legacy/.*"],
    max_depth=3,
    max_pages=500,
    max_concurrency=10,
    allowed_domains=["example.com"],
    robots_mode="strict",
    fetch_mode="hybrid",          # http | browser | hybrid
    render_js=False,              # enable for dynamic sites
    storage={
        "type": "duckdb",
        "path": "./crawler.duckdb"
    },
    output={
        "mode": "multi",          # single | multi
        "root_dir": "./out",
        "rewrite_internal_links": True,
        "generate_index": True,
        "generate_breadcrumbs": True,
        "generate_prev_next": False
    }
)

job = CrawlJob(config=config)
result = job.run()

print(result.stats)
```

⸻

DynamoDB Backend Example (PynamoDB)

```python
from ragcrawl import CrawlJob, CrawlerConfig

config = CrawlerConfig(
    seeds=["https://example.com/docs"],
    include_patterns=[r"/docs/.*"],
    max_depth=3,
    storage={
        "type": "dynamodb",
        "fail_if_unavailable": True,
        "region": "us-east-1",
        "table_prefix": "ragcrawl-prod",
        # Optional:
        # "endpoint_url": "http://localhost:8000",
        # "aws_profile": "default",
        # "ttl_days": 90,
    },
)

job = CrawlJob(config=config)
job.run()
```

⸻

Sync / Update Example

```python
from ragcrawl import SyncJob, SyncConfig

sync = SyncJob(
    SyncConfig(
        site_id="example_docs",
        strategy=["sitemap", "headers", "hash"],  # ordered preference
        max_pages=500,
        output={
            "mode": "multi",
            "root_dir": "./out",
            "rewrite_internal_links": True
        }
    )
)
sync_result = sync.run()
print(sync_result.changed_pages, sync_result.deleted_pages)
```

⸻

### Output Format Options

#### Single-Page Mode
- Writes one Markdown file (e.g., out/site.md)
- Includes TOC and per-page anchors for navigation
- Useful for small-to-medium documentation bases or offline review

#### Multi-Page Mode (Folder Structure Preserved)
- Writes one Markdown file per URL
- Preserves original folder structure under root_dir
- Rewrites internal links to local markdown paths
- Optionally generates:
    - index/TOC pages
    - breadcrumbs
    - previous/next links
- On deletions, configurable:
    - tombstone page
    - redirect stub
    - remove file

⸻

### Observability & Debuggability
- Structured logs (JSON-friendly)
- Per-run metrics:
    - discovered / fetched / succeeded / failed / skipped / changed
    - per-domain latency, retry counts, error categories
- Run artifacts:
    - crawl diagnostics per page (status codes, extraction size, timings)
- Testability requirements:
    - URL normalization unit tests
    - extraction snapshot tests
    - replayable HTTP fixtures

⸻

### Extensibility (Plugin Interfaces)

The library is designed with extension points:
- LinkFilter (custom allow/deny logic)
- Extractor (markdown/custom parsing)
- ChangeDetector (custom diff logic)
- StorageBackend (add Postgres/S3/etc.)
- Hooks:
    - on_page(document)
    - on_error(error)
    - on_change_detected(change_event)

⸻

## Project Scope (v1 vs v2)

### v1 (This Package)
- Library-first deliverable with a production-grade CLI.
- Single-machine execution with strong concurrency/backpressure controls.
- Pluggable storage:
  - DuckDB as the default centralized store (default path: `~/.ragcrawl/ragcrawl.duckdb`)
  - Optional DynamoDB backend via PynamoDB (explicitly enabled).
- Crawl features:
  - recursive crawling from seed URLs with include/exclude patterns, domain/path boundaries, URL normalization, and dedupe
  - robots/user-agent support, rate limiting, retries/backoff, redirect/canonical handling
  - HTTP / browser / hybrid fetch modes
- LLM/RAG outputs:
  - clean Markdown extraction + rich metadata + stable IDs + versioning
  - chunking (heading-aware + token/size) with chunk metadata
  - exporters (JSON/JSONL) and change events (changed/deleted/tombstones)
- Sync & change detection:
  - conditional revalidation (ETag/Last-Modified + 304)
  - optional sitemap-driven prioritization
  - content-hash diff fallback with noise reduction
- Markdown publishing:
  - single-page output with TOC/anchors
  - multi-page output preserving folder structure + internal link rewriting + optional index/breadcrumb/prev-next
- Config management:
  - `ragcrawl config` command; store settings under `~/.ragcrawl/`
  - optional Textual-based interactive TUI for config editing
- Operability:
  - structured logs, crawl/run summaries, and basic metrics counters
  - deterministic test fixtures (URL normalization + extraction snapshots)

### Near-term roadmap (v1.x)
- Full pause/resume: durable frontier persistence and resumable runs.
- Crawl policies: per-site profiles, allow/deny rulesets, and template configs.
- Content extraction improvements:
  - stronger boilerplate removal; code/doc tables preservation; improved canonical selection
  - optional PDF discovery + extraction pipeline (links first; content in later release)
- Storage & data management:
  - optional S3 content offload for large markdown with pointers in DuckDB/DynamoDB
  - pruning/retention policies for versions and tombstones
- CLI upgrades:
  - richer `ragcrawl list` / `sites` / `runs` filtering + JSON output for scripting
  - `ragcrawl doctor` diagnostics (deps, browser, permissions, network)
- LLM/Kb integrations (still optional, not coupled):
  - “export adapters” for common vector DB / embedding pipelines (LangChain/LlamaIndex connectors)
  - deterministic document IDs for idempotent re-indexing

### v2 (Scale & Automation)
- Distributed crawling / worker fleet:
  - queue-based frontier, worker autoscaling, per-domain isolation, global politeness enforcement
- Event-driven sync:
  - webhook ingest (CMS publish events), or scheduled sync service with per-site SLA
- Multi-tenant / team use:
  - shared metadata store, authn/authz, quotas, and audit logs
- Enterprise operability:
  - OpenTelemetry tracing/metrics, dashboards, and crawl health SLOs
  - run replay/debug tooling and content diff UI
- Advanced extraction:
  - structured extraction schemas, entity extraction, and “layout-aware” parsing for docs
- Native embedding & vector DB connectors (optional modules):
  - pluggable embedding providers, batching, backfills, and incremental updates

⸻

## License

RAGcrawl is licensed under the **Apache License 2.0**. See `LICENSE` for details.

### Third-party licenses & required attributions

RAGcrawl depends on third-party open-source components. You must comply with their license terms when using or redistributing RAGcrawl.

In particular, RAGcrawl uses **Crawl4AI**, which is licensed under **Apache 2.0** and includes an **attribution requirement**. When you use, distribute, or ship derivative works that include/are built on Crawl4AI, you must clearly attribute Crawl4AI in public-facing materials (e.g., README, docs, or product attribution page).

⸻

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up your development environment
- Running tests and linting
- Submitting pull requests
- Code of conduct

### Community

- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Our community standards
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Support](SUPPORT.md)** - Getting help and reporting issues
- **[Changelog](CHANGELOG.md)** - Release history and updates

### Development

- Uses `pyproject.toml` for builds (wheel + sdist)
- CI expectations:
    - lint + typecheck + unit tests
    - build verification
- Release:
    - SemVer (0.x during rapid iteration)
    - publish to PyPI on version tags
    - maintain CHANGELOG.md

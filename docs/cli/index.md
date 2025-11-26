# CLI Reference

ragcrawl provides a powerful command-line interface for all crawling operations.

## Installation

The CLI is included with the ragcrawl package:

```bash
pip install ragcrawl
ragcrawl --help
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `crawl` | Crawl a website from seed URLs |
| `sync` | Incrementally sync an existing site |
| `sites` | List all crawled sites |
| `runs` | List crawl runs for a site |
| `list` | List pages for a site |
| `config` | Manage configuration |

---

## crawl

Start a new crawl from one or more seed URLs.

### Usage

```bash
ragcrawl crawl [OPTIONS] SEEDS...
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SEEDS` | One or more seed URLs to start crawling |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-pages` | int | 100 | Maximum pages to crawl |
| `--max-depth` | int | 10 | Maximum link depth |
| `--delay` | float | 1.0 | Delay between requests (seconds) |
| `--include` | str | - | URL pattern to include (can repeat) |
| `--exclude` | str | - | URL pattern to exclude (can repeat) |
| `--output` | path | ./output | Output directory |
| `--format` | choice | multi | Output format: single, multi |
| `--db` | path | crawler.duckdb | Database file path |
| `--site-name` | str | auto | Custom name for the site |
| `--user-agent` | str | ragcrawl | Custom user agent |
| `--robots` | choice | strict | Robots mode: strict, off |
| `--browser` | flag | false | Enable browser rendering |
| `--verbose` | flag | false | Verbose output |

### Examples

**Basic crawl:**
```bash
ragcrawl crawl https://docs.example.com
```

**With limits and filters:**
```bash
ragcrawl crawl https://docs.example.com \
    --max-pages 500 \
    --max-depth 5 \
    --include "/docs/*" \
    --exclude "/api/internal/*"
```

**Custom output:**
```bash
ragcrawl crawl https://docs.example.com \
    --output ./knowledge-base \
    --format single
```

**Browser rendering for JavaScript sites:**
```bash
ragcrawl crawl https://spa.example.com --browser
```

---

## sync

Incrementally update a previously crawled site.

### Usage

```bash
ragcrawl sync [OPTIONS] SITE_ID
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SITE_ID` | Site ID to sync (from `ragcrawl sites`) |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-pages` | int | unlimited | Maximum pages to sync |
| `--max-age` | float | - | Only sync pages older than N hours |
| `--sitemap` | flag | true | Use sitemap for discovery |
| `--conditional` | flag | true | Use conditional requests |
| `--output` | path | ./output | Output directory |
| `--db` | path | crawler.duckdb | Database file path |

### Examples

**Basic sync:**
```bash
ragcrawl sync site_abc123
```

**Sync with limits:**
```bash
ragcrawl sync site_abc123 --max-pages 100 --max-age 24
```

---

## sites

List all crawled sites in the database.

### Usage

```bash
ragcrawl sites [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--db` | path | crawler.duckdb | Database file path |
| `--json` | flag | false | Output as JSON |

### Example Output

```
ID              Name                 Seeds                    Pages  Last Crawl
─────────────────────────────────────────────────────────────────────────────────
site_abc123     Example Docs         https://docs.example.com    150  2024-01-15
site_def456     API Reference        https://api.example.com      75  2024-01-14
```

---

## runs

List crawl runs for a specific site.

### Usage

```bash
ragcrawl runs [OPTIONS] SITE_ID
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SITE_ID` | Site ID to list runs for |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | int | 10 | Number of runs to show |
| `--db` | path | crawler.duckdb | Database file path |
| `--json` | flag | false | Output as JSON |

### Example Output

```
Run ID          Status     Started              Pages  Duration
───────────────────────────────────────────────────────────────
run_xyz789      completed  2024-01-15 10:30:00    150  5m 23s
run_xyz788      completed  2024-01-14 09:15:00    148  5m 10s
run_xyz787      failed     2024-01-13 08:00:00     45  2m 15s
```

---

## list

List pages for a specific site.

### Usage

```bash
ragcrawl list [OPTIONS] SITE_ID
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SITE_ID` | Site ID to list pages for |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | int | 100 | Number of pages to show |
| `--status` | int | - | Filter by HTTP status |
| `--db` | path | crawler.duckdb | Database file path |
| `--json` | flag | false | Output as JSON |

---

## config

Manage ragcrawl configuration.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `show` | Show current configuration |
| `set` | Set a configuration value |
| `reset` | Reset to defaults |
| `path` | Show config file path |

### Examples

**Show config:**
```bash
ragcrawl config show
```

**Set default database:**
```bash
ragcrawl config set db_path ./my-crawler.duckdb
```

---

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |
| `--verbose` / `-v` | Increase verbosity |
| `--quiet` / `-q` | Suppress output |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Network error |
| 4 | Storage error |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RAGCRAWL_DB_PATH` | Default database path |
| `RAGCRAWL_OUTPUT_DIR` | Default output directory |
| `RAGCRAWL_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## See Also

- [Configuration](../configuration/index.md) - Full configuration reference
- [User Guide](../user-guide/index.md) - Detailed usage guides
- [API Reference](../api/index.md) - Python API documentation

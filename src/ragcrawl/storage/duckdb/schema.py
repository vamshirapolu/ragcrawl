"""DuckDB schema definitions."""

# SQL schema for DuckDB tables

SCHEMA_SITES = """
CREATE TABLE IF NOT EXISTS sites (
    site_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    seeds JSON NOT NULL,
    allowed_domains JSON,
    allowed_subdomains BOOLEAN DEFAULT TRUE,
    config JSON,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_crawl_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    total_pages INTEGER DEFAULT 0,
    total_runs INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
"""

SCHEMA_CRAWL_RUNS = """
CREATE TABLE IF NOT EXISTS crawl_runs (
    run_id VARCHAR PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    error_message VARCHAR,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    config_snapshot JSON,
    seeds JSON,
    is_sync BOOLEAN DEFAULT FALSE,
    parent_run_id VARCHAR,
    stats JSON,
    frontier_size INTEGER DEFAULT 0,
    max_depth_reached INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_site_id ON crawl_runs(site_id);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_created_at ON crawl_runs(created_at DESC);
"""

SCHEMA_PAGES = """
CREATE TABLE IF NOT EXISTS pages (
    page_id VARCHAR PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    canonical_url VARCHAR,
    current_version_id VARCHAR,
    content_hash VARCHAR,
    etag VARCHAR,
    last_modified VARCHAR,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    last_crawled TIMESTAMP,
    last_changed TIMESTAMP,
    depth INTEGER NOT NULL,
    referrer_url VARCHAR,
    status_code INTEGER,
    is_tombstone BOOLEAN DEFAULT FALSE,
    error_count INTEGER DEFAULT 0,
    last_error VARCHAR,
    version_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pages_site_id ON pages(site_id);
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(site_id, url);
CREATE INDEX IF NOT EXISTS idx_pages_last_crawled ON pages(last_crawled);
CREATE INDEX IF NOT EXISTS idx_pages_tombstone ON pages(site_id, is_tombstone);
"""

SCHEMA_PAGE_VERSIONS = """
CREATE TABLE IF NOT EXISTS page_versions (
    version_id VARCHAR PRIMARY KEY,
    page_id VARCHAR NOT NULL,
    site_id VARCHAR NOT NULL,
    run_id VARCHAR NOT NULL,
    markdown TEXT NOT NULL,
    html TEXT,
    plain_text TEXT,
    content_hash VARCHAR NOT NULL,
    raw_hash VARCHAR,
    url VARCHAR NOT NULL,
    canonical_url VARCHAR,
    title VARCHAR,
    description VARCHAR,
    content_type VARCHAR,
    status_code INTEGER NOT NULL,
    language VARCHAR,
    headings_outline JSON,
    word_count INTEGER DEFAULT 0,
    char_count INTEGER DEFAULT 0,
    outlinks JSON,
    internal_link_count INTEGER DEFAULT 0,
    external_link_count INTEGER DEFAULT 0,
    etag VARCHAR,
    last_modified VARCHAR,
    crawled_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    fetch_latency_ms FLOAT,
    extraction_latency_ms FLOAT,
    is_tombstone BOOLEAN DEFAULT FALSE,
    extra JSON
);

CREATE INDEX IF NOT EXISTS idx_page_versions_page_id ON page_versions(page_id);
CREATE INDEX IF NOT EXISTS idx_page_versions_site_id ON page_versions(site_id);
CREATE INDEX IF NOT EXISTS idx_page_versions_run_id ON page_versions(run_id);
CREATE INDEX IF NOT EXISTS idx_page_versions_crawled_at ON page_versions(crawled_at DESC);
"""

SCHEMA_FRONTIER_ITEMS = """
CREATE TABLE IF NOT EXISTS frontier_items (
    item_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    site_id VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    normalized_url VARCHAR NOT NULL,
    url_hash VARCHAR NOT NULL,
    depth INTEGER NOT NULL,
    referrer_url VARCHAR,
    priority FLOAT DEFAULT 0.0,
    status VARCHAR NOT NULL,
    retry_count INTEGER DEFAULT 0,
    last_error VARCHAR,
    discovered_at TIMESTAMP NOT NULL,
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    domain VARCHAR NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_frontier_items_run_id ON frontier_items(run_id);
CREATE INDEX IF NOT EXISTS idx_frontier_items_status ON frontier_items(run_id, status);
CREATE INDEX IF NOT EXISTS idx_frontier_items_priority ON frontier_items(run_id, priority DESC);
"""

ALL_SCHEMAS = [
    SCHEMA_SITES,
    SCHEMA_CRAWL_RUNS,
    SCHEMA_PAGES,
    SCHEMA_PAGE_VERSIONS,
    SCHEMA_FRONTIER_ITEMS,
]


def get_all_schemas() -> list[str]:
    """Get all schema creation SQL statements."""
    return ALL_SCHEMAS

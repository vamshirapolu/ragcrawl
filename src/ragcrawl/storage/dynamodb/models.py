"""PynamoDB models for DynamoDB storage."""

from datetime import datetime
from typing import Any

from pynamodb.attributes import (
    BooleanAttribute,
    JSONAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model


class SiteUrlIndex(GlobalSecondaryIndex):
    """GSI for querying sites by URL."""

    class Meta:
        index_name = "site-url-index"
        projection = AllProjection()

    site_id = UnicodeAttribute(hash_key=True)


class SiteModel(Model):
    """DynamoDB model for Site."""

    class Meta:
        table_name = "ragcrawl-sites"
        region = "us-east-1"

    site_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    seeds = JSONAttribute()
    allowed_domains = JSONAttribute(null=True)
    allowed_subdomains = BooleanAttribute(default=True)
    config = JSONAttribute(null=True)
    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()
    last_crawl_at = UTCDateTimeAttribute(null=True)
    last_sync_at = UTCDateTimeAttribute(null=True)
    total_pages = NumberAttribute(default=0)
    total_runs = NumberAttribute(default=0)
    is_active = BooleanAttribute(default=True)


class RunSiteIndex(GlobalSecondaryIndex):
    """GSI for querying runs by site."""

    class Meta:
        index_name = "run-site-index"
        projection = AllProjection()

    site_id = UnicodeAttribute(hash_key=True)
    created_at = UTCDateTimeAttribute(range_key=True)


class CrawlRunModel(Model):
    """DynamoDB model for CrawlRun."""

    class Meta:
        table_name = "ragcrawl-runs"
        region = "us-east-1"

    run_id = UnicodeAttribute(hash_key=True)
    site_id = UnicodeAttribute()
    status = UnicodeAttribute()
    error_message = UnicodeAttribute(null=True)
    created_at = UTCDateTimeAttribute()
    started_at = UTCDateTimeAttribute(null=True)
    completed_at = UTCDateTimeAttribute(null=True)
    config_snapshot = JSONAttribute(null=True)
    seeds = JSONAttribute(null=True)
    is_sync = BooleanAttribute(default=False)
    parent_run_id = UnicodeAttribute(null=True)
    stats = JSONAttribute(null=True)
    frontier_size = NumberAttribute(default=0)
    max_depth_reached = NumberAttribute(default=0)

    site_index = RunSiteIndex()


class PageSiteIndex(GlobalSecondaryIndex):
    """GSI for querying pages by site."""

    class Meta:
        index_name = "page-site-index"
        projection = AllProjection()

    site_id = UnicodeAttribute(hash_key=True)
    last_crawled = UTCDateTimeAttribute(range_key=True)


class PageModel(Model):
    """DynamoDB model for Page."""

    class Meta:
        table_name = "ragcrawl-pages"
        region = "us-east-1"

    page_id = UnicodeAttribute(hash_key=True)
    site_id = UnicodeAttribute()
    url = UnicodeAttribute()
    canonical_url = UnicodeAttribute(null=True)
    current_version_id = UnicodeAttribute(null=True)
    content_hash = UnicodeAttribute(null=True)
    etag = UnicodeAttribute(null=True)
    last_modified = UnicodeAttribute(null=True)
    first_seen = UTCDateTimeAttribute()
    last_seen = UTCDateTimeAttribute()
    last_crawled = UTCDateTimeAttribute(null=True)
    last_changed = UTCDateTimeAttribute(null=True)
    depth = NumberAttribute()
    referrer_url = UnicodeAttribute(null=True)
    status_code = NumberAttribute(null=True)
    is_tombstone = BooleanAttribute(default=False)
    error_count = NumberAttribute(default=0)
    last_error = UnicodeAttribute(null=True)
    version_count = NumberAttribute(default=0)

    site_index = PageSiteIndex()


class VersionPageIndex(GlobalSecondaryIndex):
    """GSI for querying versions by page."""

    class Meta:
        index_name = "version-page-index"
        projection = AllProjection()

    page_id = UnicodeAttribute(hash_key=True)
    crawled_at = UTCDateTimeAttribute(range_key=True)


class PageVersionModel(Model):
    """DynamoDB model for PageVersion."""

    class Meta:
        table_name = "ragcrawl-versions"
        region = "us-east-1"

    version_id = UnicodeAttribute(hash_key=True)
    page_id = UnicodeAttribute()
    site_id = UnicodeAttribute()
    run_id = UnicodeAttribute()
    markdown = UnicodeAttribute()
    html = UnicodeAttribute(null=True)
    plain_text = UnicodeAttribute(null=True)
    content_hash = UnicodeAttribute()
    raw_hash = UnicodeAttribute(null=True)
    url = UnicodeAttribute()
    canonical_url = UnicodeAttribute(null=True)
    title = UnicodeAttribute(null=True)
    description = UnicodeAttribute(null=True)
    content_type = UnicodeAttribute(null=True)
    status_code = NumberAttribute()
    language = UnicodeAttribute(null=True)
    headings_outline = JSONAttribute(null=True)
    word_count = NumberAttribute(default=0)
    char_count = NumberAttribute(default=0)
    outlinks = JSONAttribute(null=True)
    internal_link_count = NumberAttribute(default=0)
    external_link_count = NumberAttribute(default=0)
    etag = UnicodeAttribute(null=True)
    last_modified_header = UnicodeAttribute(null=True)
    crawled_at = UTCDateTimeAttribute()
    created_at = UTCDateTimeAttribute()
    fetch_latency_ms = NumberAttribute(null=True)
    extraction_latency_ms = NumberAttribute(null=True)
    is_tombstone = BooleanAttribute(default=False)
    extra = JSONAttribute(null=True)

    page_index = VersionPageIndex()


class FrontierRunIndex(GlobalSecondaryIndex):
    """GSI for querying frontier by run."""

    class Meta:
        index_name = "frontier-run-index"
        projection = AllProjection()

    run_id = UnicodeAttribute(hash_key=True)
    priority = NumberAttribute(range_key=True)


class FrontierItemModel(Model):
    """DynamoDB model for FrontierItem."""

    class Meta:
        table_name = "ragcrawl-frontier"
        region = "us-east-1"

    item_id = UnicodeAttribute(hash_key=True)
    run_id = UnicodeAttribute()
    site_id = UnicodeAttribute()
    url = UnicodeAttribute()
    normalized_url = UnicodeAttribute()
    url_hash = UnicodeAttribute()
    depth = NumberAttribute()
    referrer_url = UnicodeAttribute(null=True)
    priority = NumberAttribute(default=0)
    status = UnicodeAttribute()
    retry_count = NumberAttribute(default=0)
    last_error = UnicodeAttribute(null=True)
    discovered_at = UTCDateTimeAttribute()
    scheduled_at = UTCDateTimeAttribute(null=True)
    started_at = UTCDateTimeAttribute(null=True)
    completed_at = UTCDateTimeAttribute(null=True)
    domain = UnicodeAttribute()

    run_index = FrontierRunIndex()

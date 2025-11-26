#!/usr/bin/env python3
"""
Sync example demonstrating incremental updates.

This example shows how to:
1. First crawl a site
2. Later sync to get only changed content
"""

import asyncio
from datetime import datetime, timezone

from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.config.sync_config import SyncConfig
from ragcrawl.core.crawl_job import CrawlJob
from ragcrawl.core.sync_job import SyncJob
from ragcrawl.storage.backend import create_storage_backend


async def initial_crawl(storage_config: StorageConfig) -> str:
    """Perform initial crawl and return site ID."""

    config = CrawlerConfig(
        seeds=["https://httpbin.org/html"],
        max_pages=10,
        max_depth=2,
        storage=storage_config,
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./sync_output",
        ),
    )

    print("=" * 50)
    print("INITIAL CRAWL")
    print("=" * 50)

    job = CrawlJob(config)
    result = await job.run()

    if result.success:
        print(f"✓ Initial crawl complete: {result.stats.pages_crawled} pages")

        # Get the site ID from storage
        backend = create_storage_backend(storage_config)
        backend.initialize()
        sites = backend.list_sites()
        backend.close()

        if sites:
            return sites[0].site_id

    return None


async def sync_site(site_id: str, storage_config: StorageConfig):
    """Sync a previously crawled site."""

    config = SyncConfig(
        site_id=site_id,

        # Sync options
        max_pages=100,
        use_sitemap=True,
        use_conditional_requests=True,

        storage=storage_config,

        # Output only changed pages
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./sync_updates",
        ),
    )

    print()
    print("=" * 50)
    print("SYNC")
    print("=" * 50)
    print(f"Site ID: {site_id}")

    job = SyncJob(config)
    result = await job.run()

    if result.success:
        print(f"\n✓ Sync complete!")
        print(f"  Pages checked: {result.stats.pages_crawled}")
        print(f"  Pages changed: {result.stats.pages_changed}")
        print(f"  Pages deleted: {result.stats.pages_deleted}")
        print(f"  Duration: {result.duration_seconds:.1f}s")

        if result.changed_pages:
            print("\nChanged pages:")
            for url in result.changed_pages[:10]:
                print(f"  - {url}")
    else:
        print(f"\n✗ Sync failed: {result.error}")


async def main():
    """Run the full example."""

    # Shared storage configuration
    storage_config = StorageConfig(
        backend=DuckDBConfig(path="./sync_example.duckdb")
    )

    # Step 1: Initial crawl
    site_id = await initial_crawl(storage_config)

    if not site_id:
        print("Failed to get site ID from initial crawl")
        return

    # Step 2: Wait a bit (in real usage, this would be hours/days later)
    print("\n⏳ Simulating time passing...")
    await asyncio.sleep(2)

    # Step 3: Sync for changes
    await sync_site(site_id, storage_config)


if __name__ == "__main__":
    asyncio.run(main())

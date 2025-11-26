#!/usr/bin/env python3
"""
DynamoDB setup and usage example.

This example demonstrates:
1. Setting up DynamoDB storage
2. Running a crawl with cloud storage
3. Querying stored data

Prerequisites:
- pip install ragcrawl[dynamodb]
- AWS credentials configured
"""

import asyncio
import os

from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DynamoDBConfig, StorageConfig
from ragcrawl.core.crawl_job import CrawlJob
from ragcrawl.storage.backend import create_storage_backend


def get_dynamodb_config() -> StorageConfig:
    """Create DynamoDB storage configuration."""

    # Option 1: Use environment variables (recommended for production)
    # export AWS_ACCESS_KEY_ID=your_key
    # export AWS_SECRET_ACCESS_KEY=your_secret
    # export AWS_DEFAULT_REGION=us-east-1

    # Option 2: For local development with DynamoDB Local
    # docker run -p 8000:8000 amazon/dynamodb-local
    use_local = os.environ.get("USE_DYNAMODB_LOCAL", "false").lower() == "true"

    if use_local:
        return StorageConfig(
            backend=DynamoDBConfig(
                table_prefix="dev-ragcrawl",
                region="us-east-1",
                endpoint_url="http://localhost:8000",
                create_tables=True,
            )
        )
    else:
        return StorageConfig(
            backend=DynamoDBConfig(
                table_prefix="ragcrawl",
                region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                create_tables=True,
            )
        )


async def crawl_with_dynamodb():
    """Run a crawl using DynamoDB storage."""

    storage_config = get_dynamodb_config()

    config = CrawlerConfig(
        seeds=["https://example.com"],
        max_pages=20,
        max_depth=2,
        storage=storage_config,
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./dynamodb_output",
        ),
    )

    print("Starting crawl with DynamoDB storage...")
    print(f"  Table prefix: {storage_config.backend.table_prefix}")
    print(f"  Region: {storage_config.backend.region}")

    job = CrawlJob(config)
    result = await job.run()

    if result.success:
        print(f"\n✓ Crawl complete: {result.stats.pages_crawled} pages")
    else:
        print(f"\n✗ Crawl failed: {result.error}")


def query_dynamodb_data():
    """Query data stored in DynamoDB."""

    storage_config = get_dynamodb_config()
    backend = create_storage_backend(storage_config)
    backend.initialize()

    print("\n--- Stored Sites ---")
    sites = backend.list_sites()
    for site in sites:
        print(f"\nSite: {site.name}")
        print(f"  ID: {site.site_id}")
        print(f"  Seeds: {site.seeds}")
        print(f"  Pages: {site.total_pages}")
        print(f"  Runs: {site.total_runs}")

        # List runs for this site
        runs = backend.list_runs(site.site_id, limit=5)
        if runs:
            print(f"\n  Recent runs:")
            for run in runs:
                print(f"    - {run.run_id}: {run.status.value}")
                print(f"      Pages: {run.stats.pages_crawled}")

        # List pages
        pages = backend.list_pages(site.site_id)
        if pages:
            print(f"\n  Sample pages ({len(pages)} total):")
            for page in pages[:5]:
                print(f"    - {page.url}")

    backend.close()


async def main():
    """Run the DynamoDB example."""

    print("=" * 60)
    print("DynamoDB Storage Example")
    print("=" * 60)

    try:
        # Check if DynamoDB is available
        storage_config = get_dynamodb_config()
        backend = create_storage_backend(storage_config)
        backend.initialize()
        backend.close()
        print("✓ DynamoDB connection successful")
    except Exception as e:
        print(f"✗ DynamoDB connection failed: {e}")
        print("\nTo use DynamoDB Local for testing:")
        print("  1. Run: docker run -p 8000:8000 amazon/dynamodb-local")
        print("  2. Set: export USE_DYNAMODB_LOCAL=true")
        return

    # Run crawl
    await crawl_with_dynamodb()

    # Query stored data
    query_dynamodb_data()


if __name__ == "__main__":
    asyncio.run(main())

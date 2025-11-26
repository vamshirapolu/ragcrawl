#!/usr/bin/env python3
"""
Quick start example using DuckDB storage.

This example demonstrates the basic usage of ragcrawl
with local DuckDB storage.
"""

import asyncio
from pathlib import Path

from ragcrawl.config.crawler_config import CrawlerConfig, FetchMode, RobotsMode
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.core.crawl_job import CrawlJob
from ragcrawl.export.json_exporter import JSONExporter


async def main():
    """Run a basic crawl with DuckDB storage."""

    # Configure the crawl
    config = CrawlerConfig(
        # Starting URLs
        seeds=["https://docs.python.org/3/tutorial/"],

        # Limits
        max_pages=50,
        max_depth=3,

        # Stay within the tutorial section
        include_patterns=[r"/3/tutorial/.*"],

        # Use HTTP mode (faster, no JS support)
        fetch_mode=FetchMode.HTTP,

        # Respect robots.txt
        robots_mode=RobotsMode.STRICT,

        # Rate limiting
        requests_per_second=2.0,
        concurrent_requests=5,

        # Local storage
        storage=StorageConfig(
            backend=DuckDBConfig(path="./python_docs.duckdb")
        ),

        # Output as separate files
        output=OutputConfig(
            mode=OutputMode.MULTI,
            root_dir="./python_docs_output",
            include_metadata=True,
            rewrite_links=True,
        ),
    )

    print("Starting crawl...")
    print(f"  Seeds: {config.seeds}")
    print(f"  Max pages: {config.max_pages}")
    print()

    # Run the crawl
    job = CrawlJob(config)
    result = await job.run()

    # Print results
    if result.success:
        print("\n✓ Crawl completed successfully!")
        print(f"  Pages crawled: {result.stats.pages_crawled}")
        print(f"  Pages failed: {result.stats.pages_failed}")
        print(f"  Duration: {result.duration_seconds:.1f}s")

        # Show sample documents
        if result.documents:
            print("\nSample pages:")
            for doc in result.documents[:5]:
                print(f"  - {doc.title or 'Untitled'}")
                print(f"    URL: {doc.url}")
                print(f"    Words: {doc.word_count}")

        # Export to JSON
        if result.documents:
            exporter = JSONExporter(indent=2)
            export_path = Path("./python_docs.json")
            exporter.export_documents(result.documents, export_path)
            print(f"\nExported to: {export_path}")

    else:
        print(f"\n✗ Crawl failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())

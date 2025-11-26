#!/usr/bin/env python3
"""
Hooks and callbacks example.

This example demonstrates:
1. Using hooks to monitor crawl progress
2. Filtering content with redaction
3. Custom processing during crawl
"""

import asyncio
import re
from typing import Dict, Optional

from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
from ragcrawl.core.crawl_job import CrawlJob
from ragcrawl.hooks.callbacks import (
    HookManager,
    OnPageCallback,
    OnErrorCallback,
    PatternRedactor,
)


class CrawlMonitor:
    """Monitor crawl progress."""

    def __init__(self):
        self.pages_crawled = 0
        self.pages_failed = 0
        self.total_chars = 0
        self.urls_seen = set()

    def on_page(self, url: str, content: str, metadata: Dict):
        """Called for each successfully crawled page."""
        self.pages_crawled += 1
        self.total_chars += len(content)
        self.urls_seen.add(url)

        # Log progress
        title = metadata.get("title", "Untitled")
        words = metadata.get("word_count", 0)
        print(f"  [{self.pages_crawled}] {title}")
        print(f"       {url}")
        print(f"       {words} words")

    def on_error(self, url: str, error: Exception):
        """Called when a page fails to crawl."""
        self.pages_failed += 1
        print(f"  [ERROR] {url}")
        print(f"          {error}")

    def summary(self):
        """Print crawl summary."""
        print("\n" + "=" * 50)
        print("CRAWL SUMMARY")
        print("=" * 50)
        print(f"Pages crawled: {self.pages_crawled}")
        print(f"Pages failed: {self.pages_failed}")
        print(f"Total characters: {self.total_chars:,}")
        print(f"Unique URLs: {len(self.urls_seen)}")


def create_redactor() -> PatternRedactor:
    """Create a redactor to remove sensitive information."""

    patterns = [
        # Email addresses
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",

        # Phone numbers (various formats)
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",

        # Social Security Numbers
        r"\b\d{3}-\d{2}-\d{4}\b",

        # API keys (generic pattern)
        r"\b[A-Za-z0-9]{32,}\b",

        # Credit card numbers (very basic)
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    ]

    return PatternRedactor(
        patterns=patterns,
        replacement="[REDACTED]"
    )


def create_content_filter():
    """Create a filter that modifies content before storage."""

    def filter_content(url: str, content: str) -> Optional[str]:
        """
        Filter and transform content.

        Return None to skip the page entirely.
        Return modified content to store.
        """

        # Skip very short content
        if len(content) < 100:
            print(f"  [SKIP] Too short: {url}")
            return None

        # Skip pages that are mostly navigation
        nav_keywords = ["skip to content", "toggle navigation", "menu"]
        content_lower = content.lower()
        nav_ratio = sum(1 for kw in nav_keywords if kw in content_lower) / len(nav_keywords)
        if nav_ratio > 0.5 and len(content) < 500:
            print(f"  [SKIP] Navigation page: {url}")
            return None

        # Clean up content
        # Remove excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Remove common footer patterns
        content = re.sub(
            r"(?i)copyright.*?\d{4}.*?all rights reserved.*?\n",
            "",
            content
        )

        return content

    return filter_content


async def main():
    """Run the hooks example."""

    print("=" * 60)
    print("Hooks and Callbacks Example")
    print("=" * 60)

    # Create monitor
    monitor = CrawlMonitor()

    # Create hook manager
    hooks = HookManager()

    # Add page callback
    hooks.on_page_crawled(monitor.on_page)

    # Add error callback
    hooks.on_error(monitor.on_error)

    # Add redactor
    redactor = create_redactor()
    hooks.add_redactor(redactor)

    # Add content filter
    content_filter = create_content_filter()
    hooks.add_content_filter(content_filter)

    # Configure crawl
    config = CrawlerConfig(
        seeds=["https://httpbin.org/html"],
        max_pages=10,
        max_depth=2,
        storage=StorageConfig(
            backend=DuckDBConfig(path="./hooks_example.duckdb")
        ),
        hooks=hooks,
    )

    print("\nStarting crawl with hooks...")
    print("-" * 50)

    job = CrawlJob(config)
    result = await job.run()

    # Print summary
    monitor.summary()

    if result.success:
        print(f"\n✓ Crawl completed successfully")
    else:
        print(f"\n✗ Crawl failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())

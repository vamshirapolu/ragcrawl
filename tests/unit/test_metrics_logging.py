"""Tests for metrics collection and logging utilities."""

import logging

from ragcrawl.utils.logging import CrawlLoggerAdapter, get_logger, setup_logging
from ragcrawl.utils.metrics import MetricsCollector


def test_metrics_collector_tracks_counts_and_rates() -> None:
    """Ensure metrics collector aggregates stats and derived metrics."""
    collector = MetricsCollector()
    collector.record_discovery(3)
    collector.record_fetch("example.com", status_code=200, latency_ms=50, bytes_downloaded=1024)
    collector.record_fetch(
        "example.com", status_code=500, latency_ms=100, bytes_downloaded=512, success=False
    )
    collector.record_extraction(25)
    collector.record_skip("filtered")
    collector.record_error("timeout", domain="example.com")
    collector.record_change(is_new=True)
    collector.record_unchanged()
    collector.record_deletion()

    metrics = collector.finalize()
    # Basic counters
    assert metrics.pages_discovered == 3
    assert metrics.pages_crawled == 2
    assert metrics.pages_succeeded == 1
    assert metrics.pages_failed == 1
    assert metrics.pages_skipped == 1
    assert metrics.pages_changed == 1
    assert metrics.pages_new == 1
    assert metrics.pages_unchanged == 1
    assert metrics.pages_deleted == 1
    # Derived values
    assert metrics.avg_fetch_latency_ms > 0
    assert metrics.pages_per_second >= 0
    domain_stats = collector.get_domain_stats()["example.com"]
    assert domain_stats["requests"] == 2
    assert domain_stats["success_rate"] == 0.5
    assert domain_stats["avg_latency_ms"] == metrics.domains["example.com"].avg_latency_ms


def test_logging_setup_and_adapter_writes_file(tmp_path) -> None:
    """setup_logging adds file handler and adapter emits log entries."""
    log_file = tmp_path / "ragcrawl.log"
    setup_logging(level=logging.INFO, json_format=True, log_file=str(log_file))

    logger = get_logger("ragcrawl.test", run_id="run1")
    logger.info("test message")

    adapter = CrawlLoggerAdapter(run_id="run1", site_id="site1")
    adapter.run_started(["https://example.com"], config_summary={"max_pages": 1})
    adapter.page_discovered("https://example.com/page", depth=1)
    adapter.page_fetched("https://example.com/page", status_code=200, latency_ms=12.5, size_bytes=100)
    adapter.page_extracted("https://example.com/page", markdown_size=50, links_found=2, latency_ms=1.2)
    adapter.page_skipped("https://example.com/page", reason="robots")
    adapter.page_failed("https://example.com/page", error="timeout", retry_count=1)
    adapter.content_changed("https://example.com/page", old_hash=None, new_hash="hash")
    adapter.tombstone_created("https://example.com/page", status_code=404)
    adapter.run_completed(stats={"pages": 1}, duration_seconds=0.5)
    adapter.run_failed("fatal error")

    assert log_file.exists()
    assert log_file.read_text()  # not empty

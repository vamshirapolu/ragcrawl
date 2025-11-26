"""Metrics collection for crawl runs."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainMetrics:
    """Metrics for a single domain."""

    requests: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_bytes: int = 0
    status_codes: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.requests == 0:
            return 0.0
        return self.total_latency_ms / self.requests

    @property
    def success_rate(self) -> float:
        """Success rate as a ratio."""
        if self.requests == 0:
            return 0.0
        return self.successes / self.requests


@dataclass
class CrawlMetrics:
    """Aggregated metrics for a crawl run."""

    # Page counts
    pages_discovered: int = 0
    pages_crawled: int = 0
    pages_succeeded: int = 0
    pages_failed: int = 0
    pages_skipped: int = 0
    pages_changed: int = 0
    pages_unchanged: int = 0
    pages_new: int = 0
    pages_deleted: int = 0

    # Performance
    total_bytes: int = 0
    total_fetch_time_ms: float = 0.0
    total_extraction_time_ms: float = 0.0

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    # Per-domain breakdown
    domains: dict[str, DomainMetrics] = field(
        default_factory=lambda: defaultdict(DomainMetrics)
    )

    # Error breakdown
    errors_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Status code breakdown
    status_codes: dict[int, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def duration_seconds(self) -> float:
        """Total duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def avg_fetch_latency_ms(self) -> float:
        """Average fetch latency."""
        if self.pages_crawled == 0:
            return 0.0
        return self.total_fetch_time_ms / self.pages_crawled

    @property
    def pages_per_second(self) -> float:
        """Crawl throughput in pages per second."""
        duration = self.duration_seconds
        if duration == 0:
            return 0.0
        return self.pages_crawled / duration

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "pages_discovered": self.pages_discovered,
            "pages_crawled": self.pages_crawled,
            "pages_succeeded": self.pages_succeeded,
            "pages_failed": self.pages_failed,
            "pages_skipped": self.pages_skipped,
            "pages_changed": self.pages_changed,
            "pages_unchanged": self.pages_unchanged,
            "pages_new": self.pages_new,
            "pages_deleted": self.pages_deleted,
            "total_bytes": self.total_bytes,
            "total_fetch_time_ms": self.total_fetch_time_ms,
            "total_extraction_time_ms": self.total_extraction_time_ms,
            "duration_seconds": self.duration_seconds,
            "avg_fetch_latency_ms": self.avg_fetch_latency_ms,
            "pages_per_second": self.pages_per_second,
            "domains_crawled": len(self.domains),
            "status_codes": dict(self.status_codes),
            "errors_by_type": dict(self.errors_by_type),
        }


class MetricsCollector:
    """
    Collector for crawl metrics with thread-safe updates.
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self.metrics = CrawlMetrics()
        self._lock_placeholder = True  # Placeholder for thread safety if needed

    def record_discovery(self, count: int = 1) -> None:
        """Record URL discovery."""
        self.metrics.pages_discovered += count

    def record_fetch(
        self,
        domain: str,
        status_code: int,
        latency_ms: float,
        bytes_downloaded: int,
        success: bool = True,
    ) -> None:
        """Record a fetch operation."""
        self.metrics.pages_crawled += 1
        self.metrics.total_bytes += bytes_downloaded
        self.metrics.total_fetch_time_ms += latency_ms
        self.metrics.status_codes[status_code] += 1

        if success:
            self.metrics.pages_succeeded += 1
        else:
            self.metrics.pages_failed += 1

        # Domain metrics
        dm = self.metrics.domains[domain]
        dm.requests += 1
        dm.total_latency_ms += latency_ms
        dm.total_bytes += bytes_downloaded
        dm.status_codes[status_code] += 1
        if success:
            dm.successes += 1
        else:
            dm.failures += 1

    def record_extraction(self, latency_ms: float) -> None:
        """Record extraction time."""
        self.metrics.total_extraction_time_ms += latency_ms

    def record_skip(self, reason: str = "filtered") -> None:
        """Record a skipped page."""
        self.metrics.pages_skipped += 1

    def record_error(self, error_type: str, domain: str | None = None) -> None:
        """Record an error."""
        self.metrics.errors_by_type[error_type] += 1
        if domain:
            self.metrics.domains[domain].errors[error_type] += 1

    def record_change(self, is_new: bool = False) -> None:
        """Record content change."""
        self.metrics.pages_changed += 1
        if is_new:
            self.metrics.pages_new += 1

    def record_unchanged(self) -> None:
        """Record unchanged page (304 or hash match)."""
        self.metrics.pages_unchanged += 1

    def record_deletion(self) -> None:
        """Record page deletion (tombstone)."""
        self.metrics.pages_deleted += 1

    def finalize(self) -> CrawlMetrics:
        """Finalize metrics and return."""
        self.metrics.end_time = time.time()
        return self.metrics

    def get_domain_stats(self) -> dict[str, dict[str, Any]]:
        """Get per-domain statistics."""
        return {
            domain: {
                "requests": dm.requests,
                "successes": dm.successes,
                "failures": dm.failures,
                "avg_latency_ms": dm.avg_latency_ms,
                "total_bytes": dm.total_bytes,
                "success_rate": dm.success_rate,
            }
            for domain, dm in self.metrics.domains.items()
        }

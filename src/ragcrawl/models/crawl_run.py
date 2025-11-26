"""CrawlRun model representing a single crawl execution."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Status of a crawl run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Completed with some errors


class CrawlStats(BaseModel):
    """Statistics for a crawl run."""

    # Page counts
    pages_discovered: int = Field(default=0, description="Total URLs discovered")
    pages_crawled: int = Field(default=0, description="Pages successfully crawled")
    pages_failed: int = Field(default=0, description="Pages that failed to crawl")
    pages_skipped: int = Field(default=0, description="Pages skipped (filtered, duplicate)")
    pages_changed: int = Field(default=0, description="Pages with content changes")
    pages_unchanged: int = Field(default=0, description="Pages without changes (304 or hash match)")
    pages_new: int = Field(default=0, description="Newly discovered pages")
    pages_deleted: int = Field(default=0, description="Pages marked as tombstones (404/410)")

    # Performance
    total_bytes_downloaded: int = Field(default=0, description="Total bytes downloaded")
    total_fetch_time_ms: float = Field(default=0.0, description="Total time spent fetching")
    total_extraction_time_ms: float = Field(default=0.0, description="Total extraction time")
    avg_fetch_latency_ms: float = Field(default=0.0, description="Average fetch latency")

    # Error breakdown
    errors_by_type: dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )
    errors_by_domain: dict[str, int] = Field(
        default_factory=dict, description="Error counts by domain"
    )

    # Status code breakdown
    status_codes: dict[int, int] = Field(
        default_factory=dict, description="Response counts by status code"
    )

    # Domain stats
    domains_crawled: set[str] = Field(
        default_factory=set, description="Unique domains crawled"
    )


class CrawlRun(BaseModel):
    """
    Represents a single crawl or sync execution.

    Tracks the status, configuration snapshot, and statistics
    for a crawl run.
    """

    # Identifiers
    run_id: str = Field(description="Unique run ID")
    site_id: str = Field(description="ID of the site being crawled")

    # Status
    status: RunStatus = Field(default=RunStatus.PENDING, description="Current run status")
    error_message: str | None = Field(default=None, description="Error message if failed")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # Configuration snapshot
    config_snapshot: dict[str, Any] = Field(
        default_factory=dict, description="Snapshot of crawler config used"
    )
    seeds: list[str] = Field(default_factory=list, description="Seed URLs for this run")

    # Run type
    is_sync: bool = Field(default=False, description="True if this is a sync/incremental run")
    parent_run_id: str | None = Field(
        default=None, description="Parent run ID for incremental syncs"
    )

    # Statistics
    stats: CrawlStats = Field(default_factory=CrawlStats)

    # Progress tracking
    frontier_size: int = Field(default=0, description="Current frontier queue size")
    max_depth_reached: int = Field(default=0, description="Maximum depth reached")

    model_config = {"frozen": False}

    def mark_started(self) -> None:
        """Mark the run as started."""
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, partial: bool = False) -> None:
        """Mark the run as completed."""
        self.status = RunStatus.PARTIAL if partial else RunStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark the run as failed."""
        self.status = RunStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()

    def mark_cancelled(self) -> None:
        """Mark the run as cancelled."""
        self.status = RunStatus.CANCELLED
        self.completed_at = datetime.now()

    @property
    def duration_seconds(self) -> float | None:
        """Get run duration in seconds."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

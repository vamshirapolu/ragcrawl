"""FrontierItem model for crawl queue state."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FrontierStatus(str, Enum):
    """Status of a frontier item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FrontierItem(BaseModel):
    """
    Represents a URL in the crawl frontier queue.

    Used for pause/resume functionality and tracking crawl progress.
    """

    # Identifiers
    item_id: str = Field(description="Unique item ID")
    run_id: str = Field(description="ID of the crawl run")
    site_id: str = Field(description="ID of the site")

    # URL info
    url: str = Field(description="URL to crawl")
    normalized_url: str = Field(description="Normalized URL for deduplication")
    url_hash: str = Field(description="Hash of normalized URL")

    # Crawl context
    depth: int = Field(ge=0, description="Depth from seed URL")
    referrer_url: str | None = Field(default=None, description="URL that linked to this")
    priority: float = Field(default=0.0, description="Crawl priority (higher = sooner)")

    # Status
    status: FrontierStatus = Field(default=FrontierStatus.PENDING)
    retry_count: int = Field(default=0, description="Number of retries attempted")
    last_error: str | None = Field(default=None, description="Last error message")

    # Timestamps
    discovered_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: datetime | None = Field(default=None, description="When scheduled for crawl")
    started_at: datetime | None = Field(default=None, description="When crawl started")
    completed_at: datetime | None = Field(default=None, description="When crawl completed")

    # Domain for rate limiting
    domain: str = Field(description="Domain for rate limiting purposes")

    model_config = {"frozen": False}

    def mark_in_progress(self) -> None:
        """Mark item as being crawled."""
        self.status = FrontierStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark item as successfully crawled."""
        self.status = FrontierStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark item as failed."""
        self.status = FrontierStatus.FAILED
        self.last_error = error
        self.retry_count += 1
        self.completed_at = datetime.now()

    def mark_skipped(self, reason: str) -> None:
        """Mark item as skipped."""
        self.status = FrontierStatus.SKIPPED
        self.last_error = reason
        self.completed_at = datetime.now()

"""Site model representing a crawl target configuration."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Site(BaseModel):
    """
    Represents a website/crawl target with its configuration.

    Stores the configuration snapshot and metadata for a crawl target.
    """

    # Identifiers
    site_id: str = Field(description="Unique site ID")
    name: str = Field(description="Human-readable site name")

    # Seed URLs
    seeds: list[str] = Field(description="Seed URLs to start crawling from")

    # Domain constraints
    allowed_domains: list[str] = Field(
        default_factory=list, description="Allowed domains to crawl"
    )
    allowed_subdomains: bool = Field(
        default=True, description="Whether to allow subdomains of allowed_domains"
    )

    # Configuration snapshot
    config: dict[str, Any] = Field(
        default_factory=dict, description="Full crawler configuration"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_crawl_at: datetime | None = Field(default=None)
    last_sync_at: datetime | None = Field(default=None)

    # Stats summary
    total_pages: int = Field(default=0, description="Total pages discovered")
    total_runs: int = Field(default=0, description="Total crawl runs")

    # Status
    is_active: bool = Field(default=True, description="Whether site is active for crawling")

    model_config = {"frozen": False}

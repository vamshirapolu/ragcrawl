"""Page model representing the current state of a crawled URL."""

from datetime import datetime

from pydantic import BaseModel, Field


class Page(BaseModel):
    """
    Represents the current state of a URL in the crawl database.

    This model tracks freshness information and points to the current
    version of the page content. It's used for incremental sync to
    determine what needs re-crawling.
    """

    # Identifiers
    page_id: str = Field(description="Stable ID: hash(normalized_url)")
    site_id: str = Field(description="ID of the site this page belongs to")

    # URLs
    url: str = Field(description="Normalized URL")
    canonical_url: str | None = Field(default=None, description="Canonical URL if different")

    # Current version pointer
    current_version_id: str | None = Field(
        default=None, description="ID of the current PageVersion"
    )
    content_hash: str | None = Field(
        default=None, description="Hash of current content for change detection"
    )

    # HTTP caching headers for conditional requests
    etag: str | None = Field(default=None, description="ETag from last response")
    last_modified: str | None = Field(
        default=None, description="Last-Modified header from last response"
    )

    # Freshness timestamps
    first_seen: datetime = Field(description="When page was first discovered")
    last_seen: datetime = Field(description="When page was last seen (in frontier or sitemap)")
    last_crawled: datetime | None = Field(
        default=None, description="When page was last successfully fetched"
    )
    last_changed: datetime | None = Field(
        default=None, description="When content was last changed"
    )

    # Crawl metadata
    depth: int = Field(ge=0, description="Minimum depth from any seed URL")
    referrer_url: str | None = Field(
        default=None, description="First URL that linked to this page"
    )

    # Status
    status_code: int | None = Field(default=None, description="Last HTTP status code")
    is_tombstone: bool = Field(
        default=False, description="True if page returned 404/410"
    )
    error_count: int = Field(default=0, description="Consecutive error count")
    last_error: str | None = Field(default=None, description="Last error message if any")

    # Version count for history
    version_count: int = Field(default=0, description="Number of versions stored")

    model_config = {"frozen": False}

    def needs_recrawl(
        self,
        max_age_hours: float | None = None,
        force: bool = False,
    ) -> bool:
        """
        Determine if this page needs to be re-crawled.

        Args:
            max_age_hours: Maximum age in hours before recrawl. None means always recrawl.
            force: If True, always return True.

        Returns:
            True if the page should be re-crawled.
        """
        if force:
            return True

        if self.is_tombstone:
            return False

        if self.last_crawled is None:
            return True

        if max_age_hours is None:
            return True

        age = datetime.now() - self.last_crawled
        return age.total_seconds() / 3600 > max_age_hours

"""Base fetcher protocol and result types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FetchStatus(str, Enum):
    """Status of a fetch operation."""

    SUCCESS = "success"
    NOT_MODIFIED = "not_modified"  # 304 response
    ERROR = "error"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"  # Robots.txt blocked
    REDIRECT = "redirect"


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    # Status
    status: FetchStatus
    status_code: int | None = None
    error: str | None = None

    # Content
    html: str | None = None
    markdown: str | None = None
    plain_text: str | None = None

    # Response metadata
    content_type: str | None = None
    content_length: int | None = None
    encoding: str | None = None

    # Caching headers
    etag: str | None = None
    last_modified: str | None = None

    # URL info
    final_url: str | None = None  # After redirects
    canonical_url: str | None = None

    # Timing
    fetch_started_at: datetime | None = None
    fetch_completed_at: datetime | None = None
    latency_ms: float = 0.0

    # Response headers (subset)
    headers: dict[str, str] = field(default_factory=dict)

    # Extraction metadata
    title: str | None = None
    description: str | None = None
    links: list[str] = field(default_factory=list)

    # Browser mode indicator
    used_browser: bool = False

    @property
    def is_success(self) -> bool:
        """Check if fetch was successful."""
        return self.status == FetchStatus.SUCCESS

    @property
    def is_not_modified(self) -> bool:
        """Check if content was not modified (304)."""
        return self.status == FetchStatus.NOT_MODIFIED

    @property
    def is_error(self) -> bool:
        """Check if fetch resulted in error."""
        return self.status in (FetchStatus.ERROR, FetchStatus.TIMEOUT)

    @property
    def is_redirect(self) -> bool:
        """Check if response was a redirect."""
        return self.status == FetchStatus.REDIRECT

    @property
    def is_client_error(self) -> bool:
        """Check if response is a client error (4xx)."""
        return self.status_code is not None and 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if response is a server error (5xx)."""
        return self.status_code is not None and 500 <= self.status_code < 600

    @property
    def is_not_found(self) -> bool:
        """Check if page was not found (404/410)."""
        return self.status_code in (404, 410)


class BaseFetcher(ABC):
    """
    Abstract base class for page fetchers.

    Fetchers are responsible for retrieving page content from URLs.
    """

    @abstractmethod
    async def fetch(
        self,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> FetchResult:
        """
        Fetch a URL and return the result.

        Args:
            url: The URL to fetch.
            etag: Optional ETag for conditional request.
            last_modified: Optional Last-Modified for conditional request.
            **kwargs: Additional fetcher-specific options.

        Returns:
            FetchResult with content and metadata.
        """
        ...

    @abstractmethod
    async def fetch_batch(
        self,
        urls: list[str],
        **kwargs: Any,
    ) -> list[FetchResult]:
        """
        Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch.
            **kwargs: Additional fetcher-specific options.

        Returns:
            List of FetchResults in the same order as input URLs.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close any resources (browser, connections, etc.)."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the fetcher is ready."""
        ...

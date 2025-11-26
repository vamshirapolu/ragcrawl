"""HTTP conditional request handling for incremental sync."""

from dataclasses import dataclass
from enum import Enum


class RevalidationStatus(str, Enum):
    """Status of revalidation check."""

    MODIFIED = "modified"  # Content changed, needs re-fetch
    NOT_MODIFIED = "not_modified"  # 304, content unchanged
    NO_VALIDATORS = "no_validators"  # No ETag/Last-Modified available
    ERROR = "error"  # Error during check


@dataclass
class RevalidationResult:
    """Result of a revalidation check."""

    status: RevalidationStatus
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None

    @property
    def needs_fetch(self) -> bool:
        """Check if full fetch is needed."""
        return self.status in (
            RevalidationStatus.MODIFIED,
            RevalidationStatus.NO_VALIDATORS,
            RevalidationStatus.ERROR,
        )


class Revalidator:
    """
    Handles HTTP conditional requests for change detection.

    Uses ETag and Last-Modified headers to efficiently detect
    content changes without downloading full content.
    """

    def __init__(
        self,
        use_etag: bool = True,
        use_last_modified: bool = True,
    ) -> None:
        """
        Initialize revalidator.

        Args:
            use_etag: Whether to use ETag for validation.
            use_last_modified: Whether to use Last-Modified.
        """
        self.use_etag = use_etag
        self.use_last_modified = use_last_modified

    def get_conditional_headers(
        self,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> dict[str, str]:
        """
        Get headers for conditional request.

        Args:
            etag: Stored ETag value.
            last_modified: Stored Last-Modified value.

        Returns:
            Dict of conditional request headers.
        """
        headers: dict[str, str] = {}

        if self.use_etag and etag:
            headers["If-None-Match"] = etag

        if self.use_last_modified and last_modified:
            headers["If-Modified-Since"] = last_modified

        return headers

    def parse_response(
        self,
        status_code: int,
        headers: dict[str, str],
    ) -> RevalidationResult:
        """
        Parse response to determine if content changed.

        Args:
            status_code: HTTP status code.
            headers: Response headers.

        Returns:
            RevalidationResult.
        """
        # Extract caching headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in headers.items()}
        etag = headers_lower.get("etag")
        last_modified = headers_lower.get("last-modified")

        if status_code == 304:
            return RevalidationResult(
                status=RevalidationStatus.NOT_MODIFIED,
                etag=etag,
                last_modified=last_modified,
            )

        if status_code >= 200 and status_code < 300:
            return RevalidationResult(
                status=RevalidationStatus.MODIFIED,
                etag=etag,
                last_modified=last_modified,
            )

        if status_code >= 400:
            return RevalidationResult(
                status=RevalidationStatus.ERROR,
                error=f"HTTP {status_code}",
            )

        return RevalidationResult(
            status=RevalidationStatus.MODIFIED,
            etag=etag,
            last_modified=last_modified,
        )

    def has_validators(
        self,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> bool:
        """
        Check if we have validators for conditional requests.

        Args:
            etag: Stored ETag.
            last_modified: Stored Last-Modified.

        Returns:
            True if we can make conditional requests.
        """
        if self.use_etag and etag:
            return True
        if self.use_last_modified and last_modified:
            return True
        return False

"""Change events for downstream consumers."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of change events."""

    PAGE_CREATED = "page_created"
    PAGE_CHANGED = "page_changed"
    PAGE_DELETED = "page_deleted"
    PAGE_UNCHANGED = "page_unchanged"


@dataclass
class ChangeEvent:
    """
    Event representing a change to a page.

    Used for notifying downstream systems of KB updates.
    """

    event_type: EventType
    page_id: str
    url: str
    site_id: str
    run_id: str
    timestamp: datetime
    version_id: str | None = None
    old_version_id: str | None = None
    content_hash: str | None = None
    old_content_hash: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type.value,
            "page_id": self.page_id,
            "url": self.url,
            "site_id": self.site_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "version_id": self.version_id,
            "old_version_id": self.old_version_id,
            "content_hash": self.content_hash,
            "old_content_hash": self.old_content_hash,
            "metadata": self.metadata,
        }


class EventEmitter:
    """
    Emits change events to registered handlers.
    """

    def __init__(self) -> None:
        """Initialize event emitter."""
        self._handlers: list[callable] = []

    def register(self, handler: callable) -> None:
        """Register an event handler."""
        self._handlers.append(handler)

    def unregister(self, handler: callable) -> None:
        """Unregister an event handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def emit(self, event: ChangeEvent) -> None:
        """Emit an event to all handlers."""
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let handler errors break the flow

    def emit_created(
        self,
        page_id: str,
        url: str,
        site_id: str,
        run_id: str,
        version_id: str,
        content_hash: str,
    ) -> None:
        """Emit page created event."""
        self.emit(ChangeEvent(
            event_type=EventType.PAGE_CREATED,
            page_id=page_id,
            url=url,
            site_id=site_id,
            run_id=run_id,
            timestamp=datetime.now(),
            version_id=version_id,
            content_hash=content_hash,
        ))

    def emit_changed(
        self,
        page_id: str,
        url: str,
        site_id: str,
        run_id: str,
        version_id: str,
        old_version_id: str | None,
        content_hash: str,
        old_content_hash: str | None,
    ) -> None:
        """Emit page changed event."""
        self.emit(ChangeEvent(
            event_type=EventType.PAGE_CHANGED,
            page_id=page_id,
            url=url,
            site_id=site_id,
            run_id=run_id,
            timestamp=datetime.now(),
            version_id=version_id,
            old_version_id=old_version_id,
            content_hash=content_hash,
            old_content_hash=old_content_hash,
        ))

    def emit_deleted(
        self,
        page_id: str,
        url: str,
        site_id: str,
        run_id: str,
    ) -> None:
        """Emit page deleted event."""
        self.emit(ChangeEvent(
            event_type=EventType.PAGE_DELETED,
            page_id=page_id,
            url=url,
            site_id=site_id,
            run_id=run_id,
            timestamp=datetime.now(),
        ))

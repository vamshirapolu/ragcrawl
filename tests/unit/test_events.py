"""Tests for change events and emitter."""

from datetime import datetime

from ragcrawl.export.events import ChangeEvent, EventEmitter, EventType


def test_change_event_to_dict() -> None:
    """ChangeEvent serializes correctly."""
    ts = datetime(2024, 1, 1, 12, 0, 0)
    event = ChangeEvent(
        event_type=EventType.PAGE_CHANGED,
        page_id="p1",
        url="https://example.com",
        site_id="s1",
        run_id="r1",
        timestamp=ts,
        version_id="v2",
        old_version_id="v1",
        content_hash="h2",
        old_content_hash="h1",
        metadata={"k": "v"},
    )
    data = event.to_dict()
    assert data["event_type"] == "page_changed"
    assert data["timestamp"] == ts.isoformat()
    assert data["metadata"] == {"k": "v"}


def test_event_emitter_register_emit_and_unregister() -> None:
    """EventEmitter dispatches to handlers and tolerates handler errors."""
    emitter = EventEmitter()
    received: list[ChangeEvent] = []

    def handler(event: ChangeEvent) -> None:
        received.append(event)

    def bad_handler(event: ChangeEvent) -> None:
        raise RuntimeError("boom")

    emitter.register(handler)
    emitter.register(bad_handler)

    emitter.emit_created(
        page_id="p1",
        url="https://example.com/page",
        site_id="s1",
        run_id="r1",
        version_id="v1",
        content_hash="h1",
    )
    assert received and received[0].event_type is EventType.PAGE_CREATED

    emitter.unregister(bad_handler)
    emitter.emit_deleted(page_id="p1", url="https://example.com/page", site_id="s1", run_id="r1")
    assert received[-1].event_type is EventType.PAGE_DELETED

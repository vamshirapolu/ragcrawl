"""Tests for SinglePagePublisher output."""

from datetime import datetime, timezone
from pathlib import Path

from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.models.document import Document
from ragcrawl.output.single_page import SinglePagePublisher


def make_doc(url: str, title: str = None, markdown: str = "# Title\n\nBody") -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        doc_id=url,
        page_id=url,
        source_url=url,
        normalized_url=url,
        markdown=markdown,
        title=title,
        status_code=200,
        depth=1,
        run_id="run1",
        site_id="site1",
        first_seen=now,
        last_seen=now,
        last_crawled=now,
    )


def test_single_page_publish_without_metadata(tmp_path) -> None:
    """Publish multiple documents with metadata header and source URL disabled."""
    config = OutputConfig(
        mode=OutputMode.SINGLE,
        root_dir=tmp_path,
        generate_toc=False,
        include_metadata_header=False,
        include_source_url=False,
        page_separator="---",
    )
    publisher = SinglePagePublisher(config)
    docs = [
        make_doc("https://example.com/a", title="A"),
        make_doc("https://example.com/b", title="B"),
    ]

    paths = publisher.publish(docs)
    assert paths == [tmp_path / config.single_file_name]
    content = paths[0].read_text()
    assert "Source:" not in content
    assert "##" not in content  # no metadata headers


def test_single_page_anchor_and_title_helpers() -> None:
    """Anchors and titles are derived from URLs."""
    config = OutputConfig(mode=OutputMode.SINGLE)
    publisher = SinglePagePublisher(config)

    assert publisher._url_to_anchor("https://example.com/") == "index"
    assert publisher._url_to_anchor("https://example.com/docs/page.md") == "docs-page-md"
    assert publisher._url_to_title("https://example.com/docs/page-name.html") == "Page Name"
    assert publisher._url_to_title("https://example.com/") == "example.com"


def test_single_page_empty_returns_empty_list(tmp_path) -> None:
    """Publishing no documents returns an empty list and writes nothing."""
    config = OutputConfig(mode=OutputMode.SINGLE, root_dir=tmp_path)
    publisher = SinglePagePublisher(config)
    assert publisher.publish([]) == []
    assert not (Path(tmp_path) / config.single_file_name).exists()
    assert publisher.publish_single(make_doc("https://example.com")) is None

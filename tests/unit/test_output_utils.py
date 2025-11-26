"""Tests for output helpers: link rewriting, navigation, and multi-page publishing."""

from datetime import datetime, timezone
from pathlib import Path

from ragcrawl.config.output_config import DeletionHandling, OutputConfig
from ragcrawl.models.document import Document
from ragcrawl.output.link_rewriter import LinkRewriter
from ragcrawl.output.multi_page import MultiPagePublisher
from ragcrawl.output.navigation import NavigationGenerator


def make_doc(url: str, title: str = "Page", markdown: str = "# Title\n\nBody") -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        doc_id=url,
        page_id=url,
        version_id="v1",
        source_url=url,
        normalized_url=url,
        canonical_url=url,
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


def test_link_rewriter_handles_internal_and_external_links(tmp_path) -> None:
    """Internal links are rewritten relative to source while others remain untouched."""
    config = OutputConfig(root_dir=tmp_path)
    rewriter = LinkRewriter(config)

    source_url = "https://example.com/docs/page"
    other_url = "https://example.com/docs/other"
    rewriter.set_url_mapping(
        {
            source_url: Path("docs/page/index.md"),
            other_url: Path("docs/other/index.md"),
        }
    )

    content = (
        "[Internal](other) [External](https://google.com) "
        "[Anchor](#section) [Mail](mailto:test@example.com)"
    )
    rewritten = rewriter.rewrite(content, source_url)
    assert "(../other/index.md)" in rewritten  # internal rewritten relative path
    assert "https://google.com" in rewritten  # external unchanged
    assert "(#section)" in rewritten  # anchor untouched
    assert "(mailto:test@example.com)" in rewritten

    # Rewriting disabled returns original content
    config.rewrite_internal_links = False
    assert rewriter.rewrite(content, source_url) == content


def test_navigation_generator_variants() -> None:
    """Breadcrumbs, prev/next, and index generation cover edge cases."""
    config = OutputConfig(generate_prev_next=True)
    nav = NavigationGenerator(config)

    root_doc = make_doc("https://example.com/")
    assert nav.generate_breadcrumbs(root_doc) == ""

    deep_doc = make_doc("https://example.com/section/page", title="Deep Page")
    crumbs = nav.generate_breadcrumbs(deep_doc)
    assert "[Home]" in crumbs and "Section" in crumbs and "Deep Page" in crumbs

    next_only = nav.generate_prev_next(prev_doc=None, next_doc=deep_doc)
    assert "**Next:**" in next_only and "**Previous:**" not in next_only

    prev_only = nav.generate_prev_next(prev_doc=deep_doc, next_doc=None)
    assert "**Previous:**" in prev_only and "**Next:**" not in prev_only

    docs = [
        deep_doc,
        make_doc("https://example.com/section/other"),
        make_doc("https://example.com/root"),
        make_doc("https://example.com/tomb", markdown="", title="",),
    ]
    docs[-1].is_tombstone = True
    index = nav.generate_index(docs)
    assert "Documentation Index" in index
    assert "tomb" not in index  # tombstone skipped


def test_multi_page_publisher_tombstones(tmp_path) -> None:
    """Tombstone handling removes, redirects, or creates tombstone pages."""
    # Remove existing file
    config_remove = OutputConfig(root_dir=tmp_path, deletion_handling=DeletionHandling.REMOVE)
    publisher = MultiPagePublisher(config_remove)
    tomb_doc = make_doc("https://example.com/delete")
    tomb_doc.is_tombstone = True
    tomb_path = publisher.output_path / publisher._url_to_path(tomb_doc.normalized_url)
    tomb_path.parent.mkdir(parents=True, exist_ok=True)
    tomb_path.write_text("stale")
    assert publisher._handle_tombstone(tomb_doc) is None
    assert not tomb_path.exists()

    # Tombstone page
    config_tomb = OutputConfig(root_dir=tmp_path, deletion_handling=DeletionHandling.TOMBSTONE)
    tomb_pub = MultiPagePublisher(config_tomb)
    tombstone = tomb_pub._handle_tombstone(tomb_doc)
    assert tombstone and tombstone.exists()
    assert "Page Removed" in tombstone.read_text()

    # Redirect page
    config_redirect = OutputConfig(root_dir=tmp_path, deletion_handling=DeletionHandling.REDIRECT)
    redirect_pub = MultiPagePublisher(config_redirect)
    redirect_path = redirect_pub._handle_tombstone(tomb_doc)
    assert redirect_path and redirect_path.exists()
    assert "redirect_to" in redirect_path.read_text()


def test_multi_page_publisher_document_output(tmp_path) -> None:
    """Publish document with metadata, breadcrumbs, and prev/next navigation."""
    config = OutputConfig(
        root_dir=tmp_path,
        include_metadata_header=True,
        generate_breadcrumbs=True,
        generate_prev_next=True,
    )
    publisher = MultiPagePublisher(config)
    doc = make_doc("https://example.com/docs/page", title='Title "Quoted"', markdown="# H1\n\nBody")
    doc.description = 'Desc "quoted"'

    prev_doc = make_doc("https://example.com/docs/prev", title="Prev")
    next_doc = make_doc("https://example.com/docs/next", title="Next")

    path = publisher._publish_document(doc, prev_doc, next_doc)
    content = path.read_text()
    assert 'title: "Title \\"Quoted\\""' in content
    assert 'description: "Desc \\"quoted\\""' in content
    assert "Source:" in content
    assert "Previous:" in content and "Next:" in content


def test_url_to_path_variations() -> None:
    """_url_to_path handles roots, extensions, and directory-style URLs."""
    config = OutputConfig()
    publisher = MultiPagePublisher(config)

    assert publisher._url_to_path("https://example.com/") == Path("index.md")
    assert publisher._url_to_path("https://example.com/about") == Path("about/index.md")
    assert publisher._url_to_path("https://example.com/file.html") == Path("file/index.md")
    assert publisher._url_to_path("https://example.com/file.txt") == Path("file.txt.md")

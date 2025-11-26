"""Tests for link filtering."""

import pytest

from ragcrawl.filters.link_filter import LinkFilter, FilterReason


class TestLinkFilter:
    """Tests for LinkFilter."""

    def test_filter_same_domain(self) -> None:
        """Test filtering links to same domain."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            allow_subdomains=True,
        )

        result = link_filter.filter("https://example.com/page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://sub.example.com/page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://other.com/page", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.DOMAIN_NOT_ALLOWED

    def test_filter_without_subdomains(self) -> None:
        """Test filtering without allowing subdomains."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            allow_subdomains=False,
        )

        result = link_filter.filter("https://example.com/page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://sub.example.com/page", check_seen=False)
        assert not result.allowed

    def test_filter_include_patterns(self) -> None:
        """Test include pattern filtering."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            include_patterns=["/docs/*", "/api/*"],
        )

        result = link_filter.filter("https://example.com/docs/guide", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/api/v1", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/blog/post", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.NO_INCLUDE_MATCH

    def test_filter_exclude_patterns(self) -> None:
        """Test exclude pattern filtering."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            exclude_patterns=["/admin/*", "/private/*"],
        )

        result = link_filter.filter("https://example.com/docs/guide", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/admin/dashboard", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.EXCLUDED_PATTERN

        result = link_filter.filter("https://example.com/private/data", check_seen=False)
        assert not result.allowed

    def test_filter_exclude_takes_precedence(self) -> None:
        """Test that exclude patterns take precedence over include."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            include_patterns=["/docs/*"],
            exclude_patterns=["*secret*"],
        )

        result = link_filter.filter("https://example.com/docs/guide", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/docs/secret", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.EXCLUDED_PATTERN

    def test_filter_max_depth(self) -> None:
        """Test max depth filtering."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
        )

        result = link_filter.filter("https://example.com/page", check_seen=False, current_depth=1, max_depth=2)
        assert result.allowed

        result = link_filter.filter("https://example.com/page", check_seen=False, current_depth=2, max_depth=2)
        assert result.allowed

        result = link_filter.filter("https://example.com/page", check_seen=False, current_depth=3, max_depth=2)
        assert not result.allowed
        assert result.reason == FilterReason.MAX_DEPTH_EXCEEDED

    def test_filter_skip_binary_extensions(self) -> None:
        """Test skipping binary file extensions when configured."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            blocked_extensions=[".pdf", ".png", ".docx"],
        )

        result = link_filter.filter("https://example.com/page.html", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/file.pdf", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.BLOCKED_EXTENSION

        result = link_filter.filter("https://example.com/image.png", check_seen=False)
        assert not result.allowed

        result = link_filter.filter("https://example.com/doc.docx", check_seen=False)
        assert not result.allowed

    def test_filter_custom_skip_extensions(self) -> None:
        """Test custom skip extensions."""
        link_filter = LinkFilter(
            allowed_domains=["example.com"],
            blocked_extensions=[".custom", ".skip"],
        )

        result = link_filter.filter("https://example.com/file.custom", check_seen=False)
        assert not result.allowed

        result = link_filter.filter("https://example.com/file.skip", check_seen=False)
        assert not result.allowed

    def test_filter_multiple_domains(self) -> None:
        """Test multiple allowed domains."""
        link_filter = LinkFilter(
            allowed_domains=["example.com", "docs.example.org"],
        )

        result = link_filter.filter("https://example.com/page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://docs.example.org/page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://other.com/page", check_seen=False)
        assert not result.allowed

    def test_filter_normalize_url(self) -> None:
        """Test URL normalization in filtering."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        result = link_filter.filter("HTTPS://EXAMPLE.COM/Page", check_seen=False)
        assert result.allowed

        result = link_filter.filter("https://example.com/page?utm_source=test", check_seen=False)
        assert result.allowed

    def test_filter_empty_url(self) -> None:
        """Test handling of empty URLs."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        result = link_filter.filter("", check_seen=False)
        assert not result.allowed
        assert result.reason == FilterReason.INVALID_URL

    def test_filter_javascript_url(self) -> None:
        """Test filtering javascript URLs."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        result = link_filter.filter("javascript:void(0)", check_seen=False)
        assert not result.allowed
        # javascript: URLs have no netloc, so they're invalid URLs
        assert result.reason == FilterReason.INVALID_URL

    def test_filter_mailto_url(self) -> None:
        """Test filtering mailto URLs."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        result = link_filter.filter("mailto:test@example.com", check_seen=False)
        assert not result.allowed
        # mailto: URLs have no netloc, so they're invalid URLs
        assert result.reason == FilterReason.INVALID_URL

    def test_filter_data_url(self) -> None:
        """Test filtering data URLs."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        result = link_filter.filter("data:text/html,<h1>Hello</h1>", check_seen=False)
        assert not result.allowed
        # data: URLs have no netloc, so they're invalid URLs
        assert result.reason == FilterReason.INVALID_URL

    def test_mark_and_check_seen(self) -> None:
        """Test marking URLs as seen."""
        link_filter = LinkFilter(allowed_domains=["example.com"])

        url = "https://example.com/page"
        assert not link_filter.is_seen(url)

        link_filter.mark_seen(url)
        assert link_filter.is_seen(url)

        result = link_filter.filter(url, check_seen=True)
        assert not result.allowed
        assert result.reason == FilterReason.ALREADY_SEEN

"""Tests for pattern matching."""

import pytest

from ragcrawl.filters.patterns import ExtensionFilter, PatternMatcher


class TestPatternMatcher:
    """Tests for PatternMatcher."""

    def test_include_pattern_match(self) -> None:
        """Test include pattern matching."""
        # Use glob patterns (the implementation auto-detects)
        matcher = PatternMatcher(include_patterns=["/docs/*", "/api/*"])

        assert matcher.should_include("/docs/guide")
        assert matcher.should_include("/api/v1/users")
        assert not matcher.should_include("/blog/post")

    def test_exclude_pattern_match(self) -> None:
        """Test exclude pattern matching."""
        matcher = PatternMatcher(exclude_patterns=["/admin/*", "/private/*"])

        assert matcher.should_include("/docs/guide")
        assert not matcher.should_include("/admin/settings")
        assert not matcher.should_include("/private/data")

    def test_exclude_takes_precedence(self) -> None:
        """Test that exclude patterns take precedence."""
        matcher = PatternMatcher(
            include_patterns=["/docs/*"],
            exclude_patterns=["*secret*"],
        )

        assert matcher.should_include("/docs/public")
        assert not matcher.should_include("/docs/secret-info")

    def test_no_patterns_allow_all(self) -> None:
        """Test that no patterns allows all URLs."""
        matcher = PatternMatcher()

        assert matcher.should_include("/anything/goes")
        assert matcher.should_include("/docs/page")

    def test_case_sensitive_patterns(self) -> None:
        """Test case-sensitive pattern matching."""
        matcher = PatternMatcher(
            include_patterns=["/Docs/*"],
            case_sensitive=True,
        )

        assert matcher.should_include("/Docs/Guide")
        assert not matcher.should_include("/docs/guide")

    def test_case_insensitive_patterns(self) -> None:
        """Test case-insensitive pattern matching."""
        matcher = PatternMatcher(
            include_patterns=["/docs/*"],
            case_sensitive=False,
        )

        assert matcher.should_include("/docs/guide")
        assert matcher.should_include("/DOCS/GUIDE")
        assert matcher.should_include("/Docs/Guide")

    def test_full_url_patterns(self) -> None:
        """Test patterns against full URLs."""
        matcher = PatternMatcher(
            include_patterns=["https://example.com/docs/*"],
        )

        assert matcher.should_include("https://example.com/docs/guide")
        assert not matcher.should_include("https://other.com/docs/guide")

    def test_complex_regex_patterns(self) -> None:
        """Test complex regex patterns using regex-specific chars."""
        # Use | to force regex interpretation
        matcher = PatternMatcher(
            include_patterns=[r"/api/v(1|2)/.*"],
        )

        assert matcher.should_include("/api/v1/users")
        assert matcher.should_include("/api/v2/products")
        assert not matcher.should_include("/api/beta/users")

    def test_invalid_regex_handled_as_literal(self) -> None:
        """Test handling of invalid regex patterns as literals."""
        # Invalid regex is handled gracefully by escaping
        matcher = PatternMatcher(include_patterns=[r"[invalid"])
        # Should not raise, treats as literal
        assert not matcher.should_include("/docs/guide")


class TestExtensionFilter:
    """Tests for ExtensionFilter."""

    def test_blocked_extensions(self) -> None:
        """Test blocked extension detection."""
        ext_filter = ExtensionFilter(blocked_extensions=[".pdf", ".zip", ".png"])

        assert ext_filter.is_blocked("https://example.com/file.pdf")
        assert ext_filter.is_blocked("https://example.com/file.zip")
        assert ext_filter.is_blocked("https://example.com/image.png")
        assert not ext_filter.is_blocked("https://example.com/page.html")

    def test_no_extension_not_blocked(self) -> None:
        """Test that URLs without extensions are not blocked."""
        ext_filter = ExtensionFilter(blocked_extensions=[".pdf"])

        assert not ext_filter.is_blocked("https://example.com/page")
        assert not ext_filter.is_blocked("https://example.com/page?query=1")

    def test_custom_blocked_extensions(self) -> None:
        """Test custom blocked extensions."""
        ext_filter = ExtensionFilter(blocked_extensions=[".custom", ".myext"])

        assert ext_filter.is_blocked("https://example.com/file.custom")
        assert ext_filter.is_blocked("https://example.com/file.myext")
        assert not ext_filter.is_blocked("https://example.com/page.html")

    def test_extension_case_insensitive(self) -> None:
        """Test case-insensitive extension matching."""
        ext_filter = ExtensionFilter(blocked_extensions=[".pdf"])

        assert ext_filter.is_blocked("https://example.com/file.PDF")
        assert ext_filter.is_blocked("https://example.com/file.Pdf")

    def test_get_extension(self) -> None:
        """Test extension extraction."""
        ext_filter = ExtensionFilter()

        assert ext_filter.get_extension("https://example.com/page.html") == ".html"
        assert ext_filter.get_extension("https://example.com/page") is None
        assert ext_filter.get_extension("https://example.com/file.tar.gz") == ".gz"

    def test_empty_blocked_extensions(self) -> None:
        """Test that empty blocked list blocks nothing."""
        ext_filter = ExtensionFilter()

        assert not ext_filter.is_blocked("https://example.com/file.pdf")
        assert not ext_filter.is_blocked("https://example.com/file.zip")

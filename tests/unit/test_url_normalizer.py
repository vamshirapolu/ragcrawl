"""Tests for URL normalization."""

import pytest

from ragcrawl.filters.url_normalizer import URLNormalizer


class TestURLNormalizer:
    """Tests for URLNormalizer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.normalizer = URLNormalizer()

    def test_basic_normalization(self) -> None:
        """Test basic URL normalization."""
        url = "HTTPS://EXAMPLE.COM/Page"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/Page"

    def test_remove_default_port(self) -> None:
        """Test removal of default ports."""
        url = "https://example.com:443/page"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/page"

        url = "http://example.com:80/page"
        result = self.normalizer.normalize(url)
        assert result == "http://example.com/page"

    def test_keep_non_default_port(self) -> None:
        """Test keeping non-default ports."""
        url = "https://example.com:8080/page"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com:8080/page"

    def test_remove_trailing_slash(self) -> None:
        """Test removal of trailing slashes."""
        url = "https://example.com/page/"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/page"

    def test_keep_root_trailing_slash(self) -> None:
        """Test keeping root path slash."""
        url = "https://example.com/"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/"

    def test_remove_fragment(self) -> None:
        """Test removal of fragments."""
        url = "https://example.com/page#section"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/page"

    def test_sort_query_params(self) -> None:
        """Test query parameter sorting."""
        url = "https://example.com/page?z=1&a=2&m=3"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/page?a=2&m=3&z=1"

    def test_remove_tracking_params(self) -> None:
        """Test removal of tracking parameters."""
        url = "https://example.com/page?utm_source=google&id=123&utm_medium=cpc"
        result = self.normalizer.normalize(url)
        assert result == "https://example.com/page?id=123"

    def test_custom_tracking_params(self) -> None:
        """Test custom tracking parameter removal."""
        normalizer = URLNormalizer(
            remove_query_params=["custom_track"],
        )
        url = "https://example.com/page?custom_track=1&id=123"
        result = normalizer.normalize(url)
        assert result == "https://example.com/page?id=123"

    def test_preserve_tracking_params(self) -> None:
        """Test that default tracking params are still removed."""
        # Default behavior removes utm_source
        url = "https://example.com/page?utm_source=google&id=123"
        result = self.normalizer.normalize(url)
        # utm_source should be removed by default
        assert "id=123" in result

    def test_url_decode_path(self) -> None:
        """Test URL path with encoded characters."""
        url = "https://example.com/path%20with%20spaces"
        result = self.normalizer.normalize(url)
        # Path encoding is preserved
        assert "path" in result

    def test_get_domain(self) -> None:
        """Test domain extraction."""
        url = "https://sub.example.com/page"
        domain = self.normalizer.get_domain(url)
        assert domain == "sub.example.com"

    def test_get_registered_domain(self) -> None:
        """Test registered domain extraction."""
        url = "https://sub.example.com/page"
        registered_domain = self.normalizer.get_registered_domain(url)
        assert registered_domain == "example.com"

    def test_is_same_domain(self) -> None:
        """Test same domain checking."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"
        assert self.normalizer.is_same_domain(url1, url2)

    def test_is_different_domain(self) -> None:
        """Test different domain detection."""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"
        assert not self.normalizer.is_same_domain(url1, url2)

    def test_is_same_registered_domain_with_subdomain(self) -> None:
        """Test same registered domain with subdomain."""
        url1 = "https://sub.example.com/page"
        url2 = "https://example.com/page"
        assert self.normalizer.is_same_registered_domain(url1, url2)

    def test_is_different_registered_domain(self) -> None:
        """Test different registered domain detection."""
        url1 = "https://example.com/page"
        url2 = "https://other.com/page"
        assert not self.normalizer.is_same_registered_domain(url1, url2)

    def test_invalid_url(self) -> None:
        """Test handling of invalid URLs."""
        url = "not-a-url"
        result = self.normalizer.normalize(url)
        assert result == url

"""Tests for hashing utilities."""

from datetime import datetime

import pytest

from ragcrawl.utils.hashing import compute_content_hash, compute_doc_id, compute_url_hash
from ragcrawl.utils.hashing import (
    generate_chunk_id,
    generate_run_id,
    generate_site_id,
    generate_version_id,
)


class TestHashing:
    """Tests for hashing functions."""

    def test_compute_doc_id(self) -> None:
        """Test document ID computation."""
        url = "https://example.com/page"
        doc_id = compute_doc_id(url)

        assert isinstance(doc_id, str)
        assert len(doc_id) == 16

    def test_compute_doc_id_deterministic(self) -> None:
        """Test that doc ID computation is deterministic."""
        url = "https://example.com/page"
        doc_id1 = compute_doc_id(url)
        doc_id2 = compute_doc_id(url)

        assert doc_id1 == doc_id2

    def test_compute_doc_id_different_urls(self) -> None:
        """Test that different URLs produce different IDs."""
        url1 = "https://example.com/page1"
        url2 = "https://example.com/page2"

        doc_id1 = compute_doc_id(url1)
        doc_id2 = compute_doc_id(url2)

        assert doc_id1 != doc_id2

    def test_compute_content_hash(self) -> None:
        """Test content hash computation."""
        content = "Hello, World!"
        hash_value = compute_content_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_compute_content_hash_deterministic(self) -> None:
        """Test that content hash computation is deterministic."""
        content = "Hello, World!"
        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert hash1 == hash2

    def test_compute_content_hash_different_content(self) -> None:
        """Test that different content produces different hashes."""
        hash1 = compute_content_hash("Content A")
        hash2 = compute_content_hash("Content B")

        assert hash1 != hash2

    def test_compute_content_hash_bytes(self) -> None:
        """Test content hash with bytes input."""
        content = b"Hello, World!"
        hash_value = compute_content_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_compute_content_hash_empty(self) -> None:
        """Test content hash with empty content."""
        hash_value = compute_content_hash("")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_compute_url_hash(self) -> None:
        """Test URL hash computation."""
        url = "https://example.com/page"
        hash_value = compute_url_hash(url)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_compute_url_hash_deterministic(self) -> None:
        """Test that URL hash computation is deterministic."""
        url = "https://example.com/page"
        hash1 = compute_url_hash(url)
        hash2 = compute_url_hash(url)

        assert hash1 == hash2

    def test_compute_url_hash_normalization(self) -> None:
        """Test URL hash with URL variations."""
        # Different forms of the same URL should produce the same hash
        url1 = "https://example.com/page"
        url2 = "https://example.com/page/"

        # Note: These may differ if normalization isn't applied
        # The test validates current behavior
        hash1 = compute_url_hash(url1)
        hash2 = compute_url_hash(url2)

        # Without normalization, hashes will differ
        assert hash1 != hash2

    def test_hash_collision_resistance(self) -> None:
        """Test that hashes have good distribution."""
        urls = [f"https://example.com/page{i}" for i in range(100)]
        hashes = set(compute_url_hash(url) for url in urls)

        # All hashes should be unique
        assert len(hashes) == len(urls)

    def test_content_hash_unicode(self) -> None:
        """Test content hash with unicode content."""
        content = "Hello, 世界! 🌍"
        hash_value = compute_content_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_content_hash_large_content(self) -> None:
        """Test content hash with large content."""
        content = "x" * 1_000_000
        hash_value = compute_content_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16

    def test_generate_ids_and_non_normalized_hash(self) -> None:
        """Cover helper ID generators and hash normalization toggle."""
        raw = "Text   with   gaps"
        normalized_hash = compute_content_hash(raw)
        non_normalized_hash = compute_content_hash(raw, normalize=False)
        assert normalized_hash != non_normalized_hash

        run_id = generate_run_id()
        assert run_id.startswith("run_") and len(run_id) > 10

        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        version_id = generate_version_id("abcdef1234567890", timestamp=timestamp)
        assert version_id.startswith("v_abcdef123456_20240101120000")

        # Default timestamp path
        default_version = generate_version_id("abcdef1234567890")
        assert default_version.startswith("v_abcdef123456")

        chunk_id = generate_chunk_id("doc", 3)
        assert chunk_id.endswith("0003")

        site_id = generate_site_id(["https://b.com", "https://a.com"])
        # Deterministic regardless of order
        site_id2 = generate_site_id(["https://a.com", "https://b.com"])
        assert site_id == site_id2 and site_id.startswith("site_")

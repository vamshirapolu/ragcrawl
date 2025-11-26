"""Hashing utilities for stable ID generation."""

import re
import uuid
from datetime import datetime

import xxhash


def compute_doc_id(normalized_url: str) -> str:
    """
    Compute a stable document ID from a normalized URL.

    Uses xxhash for fast, deterministic hashing.

    Args:
        normalized_url: The normalized URL string.

    Returns:
        A hex string ID that's stable across runs.
    """
    return xxhash.xxh64(normalized_url.encode("utf-8")).hexdigest()


def compute_url_hash(url: str) -> str:
    """
    Compute a hash of a URL.

    This is an alias for compute_doc_id for semantic clarity.

    Args:
        url: The URL to hash.

    Returns:
        A hex string hash of the URL.
    """
    return compute_doc_id(url)


def compute_content_hash(content: str | bytes, normalize: bool = True) -> str:
    """
    Compute a hash of content for change detection.

    Args:
        content: The content to hash (typically Markdown). Can be str or bytes.
        normalize: If True, normalize whitespace before hashing (only for str).

    Returns:
        A hex string hash of the content.
    """
    if isinstance(content, bytes):
        return xxhash.xxh64(content).hexdigest()

    if normalize:
        # Normalize whitespace to reduce false positives
        content = re.sub(r"\s+", " ", content.strip())

    return xxhash.xxh64(content.encode("utf-8")).hexdigest()


def generate_run_id() -> str:
    """
    Generate a unique run ID.

    Format: run_{timestamp}_{random}

    Returns:
        A unique run identifier.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = uuid.uuid4().hex[:8]
    return f"run_{timestamp}_{random_suffix}"


def generate_version_id(content_hash: str, timestamp: datetime | None = None) -> str:
    """
    Generate a version ID from content hash and timestamp.

    Args:
        content_hash: Hash of the content.
        timestamp: Optional timestamp (defaults to now).

    Returns:
        A version identifier.
    """
    if timestamp is None:
        timestamp = datetime.now()

    ts_str = timestamp.strftime("%Y%m%d%H%M%S")
    return f"v_{content_hash[:12]}_{ts_str}"


def generate_chunk_id(doc_id: str, chunk_index: int) -> str:
    """
    Generate a chunk ID from document ID and index.

    Args:
        doc_id: Parent document ID.
        chunk_index: Index of the chunk (0-based).

    Returns:
        A unique chunk identifier.
    """
    return f"{doc_id}_chunk_{chunk_index:04d}"


def generate_site_id(seed_urls: list[str]) -> str:
    """
    Generate a site ID from seed URLs.

    Args:
        seed_urls: List of seed URLs.

    Returns:
        A stable site identifier based on seeds.
    """
    # Sort and join for determinism
    seeds_str = "|".join(sorted(seed_urls))
    hash_val = xxhash.xxh64(seeds_str.encode("utf-8")).hexdigest()[:12]
    return f"site_{hash_val}"

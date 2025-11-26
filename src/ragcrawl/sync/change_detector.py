"""Content change detection for incremental sync."""

import re
from typing import Protocol

from ragcrawl.utils.hashing import compute_content_hash


class ChangeDetectorProtocol(Protocol):
    """Protocol for change detectors."""

    def has_changed(self, old_hash: str | None, new_hash: str) -> bool:
        """Check if content has changed."""
        ...

    def compute_hash(self, content: str) -> str:
        """Compute content hash."""
        ...


class ChangeDetector:
    """
    Detects content changes using hash comparison.

    Supports noise reduction to minimize false positives from
    dynamic content like dates, timestamps, etc.
    """

    def __init__(
        self,
        normalize: bool = True,
        noise_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize change detector.

        Args:
            normalize: Whether to normalize content before hashing.
            noise_patterns: Regex patterns for noise to strip before hashing.
        """
        self.normalize = normalize
        self.noise_patterns = self._compile_patterns(noise_patterns or [])

    def _compile_patterns(self, patterns: list[str]) -> list[re.Pattern[str]]:
        """Compile noise patterns."""
        compiled = []
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                pass
        return compiled

    def has_changed(self, old_hash: str | None, new_hash: str) -> bool:
        """
        Check if content has changed.

        Args:
            old_hash: Previous content hash (None if new page).
            new_hash: New content hash.

        Returns:
            True if content has changed.
        """
        if old_hash is None:
            return True

        return old_hash != new_hash

    def compute_hash(self, content: str) -> str:
        """
        Compute content hash with optional normalization.

        Args:
            content: Content to hash.

        Returns:
            Content hash.
        """
        processed = content

        # Apply noise reduction
        for pattern in self.noise_patterns:
            processed = pattern.sub("", processed)

        # Compute hash
        return compute_content_hash(processed, normalize=self.normalize)

    def get_diff_ratio(self, old_content: str, new_content: str) -> float:
        """
        Calculate similarity ratio between old and new content.

        Args:
            old_content: Previous content.
            new_content: New content.

        Returns:
            Ratio between 0 (completely different) and 1 (identical).
        """
        from difflib import SequenceMatcher

        # Normalize both
        if self.normalize:
            old_content = re.sub(r"\s+", " ", old_content.strip())
            new_content = re.sub(r"\s+", " ", new_content.strip())

        return SequenceMatcher(None, old_content, new_content).ratio()

    def is_significant_change(
        self,
        old_content: str,
        new_content: str,
        threshold: float = 0.1,
    ) -> bool:
        """
        Check if change is significant (not just noise).

        Args:
            old_content: Previous content.
            new_content: New content.
            threshold: Minimum change ratio to be significant.

        Returns:
            True if change is significant.
        """
        ratio = self.get_diff_ratio(old_content, new_content)
        change_ratio = 1 - ratio
        return change_ratio >= threshold


class ContentNormalizer:
    """
    Normalizes content for consistent change detection.
    """

    def __init__(
        self,
        strip_whitespace: bool = True,
        lowercase: bool = False,
        strip_patterns: list[str] | None = None,
    ) -> None:
        """
        Initialize normalizer.

        Args:
            strip_whitespace: Normalize whitespace.
            lowercase: Convert to lowercase.
            strip_patterns: Patterns to strip.
        """
        self.strip_whitespace = strip_whitespace
        self.lowercase = lowercase
        self.strip_patterns = self._compile_patterns(strip_patterns or [])

    def _compile_patterns(self, patterns: list[str]) -> list[re.Pattern[str]]:
        """Compile patterns."""
        compiled = []
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                pass
        return compiled

    def normalize(self, content: str) -> str:
        """
        Normalize content.

        Args:
            content: Content to normalize.

        Returns:
            Normalized content.
        """
        result = content

        # Strip patterns
        for pattern in self.strip_patterns:
            result = pattern.sub("", result)

        # Whitespace normalization
        if self.strip_whitespace:
            result = re.sub(r"\s+", " ", result)
            result = result.strip()

        # Lowercase
        if self.lowercase:
            result = result.lower()

        return result

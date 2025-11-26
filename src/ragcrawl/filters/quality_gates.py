"""Content quality gates for filtering low-value pages."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class QualityIssue(str, Enum):
    """Types of quality issues."""

    PASSED = "passed"
    TOO_SHORT = "too_short"
    LOW_WORD_COUNT = "low_word_count"
    BLOCKED_PATTERN = "blocked_pattern"
    DUPLICATE_CONTENT = "duplicate_content"
    WRONG_LANGUAGE = "wrong_language"
    THIN_CONTENT = "thin_content"


@dataclass
class QualityResult:
    """Result of quality gate evaluation."""

    passed: bool
    issue: QualityIssue
    details: str | None = None
    metrics: dict[str, Any] | None = None


class QualityGate:
    """
    Evaluates content quality to filter thin/low-value pages.
    """

    def __init__(
        self,
        min_text_length: int = 100,
        min_word_count: int = 20,
        max_duplicate_ratio: float = 0.9,
        block_patterns: list[str] | None = None,
        detect_language: bool = False,
        allowed_languages: list[str] | None = None,
    ) -> None:
        """
        Initialize quality gates.

        Args:
            min_text_length: Minimum text length in characters.
            min_word_count: Minimum word count.
            max_duplicate_ratio: Maximum ratio of duplicate content.
            block_patterns: URL patterns for thin/low-value pages.
            detect_language: Whether to detect language.
            allowed_languages: Allowed language codes (None = all).
        """
        self.min_text_length = min_text_length
        self.min_word_count = min_word_count
        self.max_duplicate_ratio = max_duplicate_ratio
        self.detect_language = detect_language
        self.allowed_languages = set(allowed_languages or [])

        # Compile block patterns
        self.block_patterns = []
        for pattern in block_patterns or []:
            try:
                self.block_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                pass

        # Content hash cache for duplicate detection
        self._content_hashes: dict[str, str] = {}

    def check_url(self, url: str) -> QualityResult:
        """
        Check if URL matches any block patterns.

        Args:
            url: The URL to check.

        Returns:
            QualityResult.
        """
        for pattern in self.block_patterns:
            if pattern.search(url):
                return QualityResult(
                    passed=False,
                    issue=QualityIssue.BLOCKED_PATTERN,
                    details=f"URL matches block pattern: {pattern.pattern}",
                )

        return QualityResult(passed=True, issue=QualityIssue.PASSED)

    def check_content(
        self,
        content: str,
        url: str | None = None,
        content_hash: str | None = None,
    ) -> QualityResult:
        """
        Check if content passes quality gates.

        Args:
            content: The text/markdown content.
            url: Optional URL for context.
            content_hash: Optional pre-computed content hash.

        Returns:
            QualityResult.
        """
        # Length check
        text_length = len(content)
        if text_length < self.min_text_length:
            return QualityResult(
                passed=False,
                issue=QualityIssue.TOO_SHORT,
                details=f"Content length {text_length} < {self.min_text_length}",
                metrics={"text_length": text_length},
            )

        # Word count check
        word_count = len(content.split())
        if word_count < self.min_word_count:
            return QualityResult(
                passed=False,
                issue=QualityIssue.LOW_WORD_COUNT,
                details=f"Word count {word_count} < {self.min_word_count}",
                metrics={"word_count": word_count},
            )

        # Duplicate content check
        if content_hash:
            if content_hash in self._content_hashes:
                original_url = self._content_hashes[content_hash]
                return QualityResult(
                    passed=False,
                    issue=QualityIssue.DUPLICATE_CONTENT,
                    details=f"Duplicate of {original_url}",
                    metrics={"original_url": original_url},
                )

            if url:
                self._content_hashes[content_hash] = url

        # Language detection (optional)
        if self.detect_language and self.allowed_languages:
            detected_lang = self._detect_language(content)
            if detected_lang and detected_lang not in self.allowed_languages:
                return QualityResult(
                    passed=False,
                    issue=QualityIssue.WRONG_LANGUAGE,
                    details=f"Language '{detected_lang}' not in allowed list",
                    metrics={"detected_language": detected_lang},
                )

        return QualityResult(
            passed=True,
            issue=QualityIssue.PASSED,
            metrics={
                "text_length": text_length,
                "word_count": word_count,
            },
        )

    def _detect_language(self, content: str) -> str | None:
        """
        Detect the language of content.

        Args:
            content: The text content.

        Returns:
            Language code or None.
        """
        # Simple heuristic-based detection
        # For production, consider using langdetect or similar
        try:
            # Sample first 1000 chars
            sample = content[:1000].lower()

            # Check for common language indicators
            if any(
                word in sample
                for word in ["the", "and", "is", "are", "was", "were", "have", "has"]
            ):
                return "en"

            # Add more language detection as needed
            return None

        except Exception:
            return None

    def check_all(
        self,
        url: str,
        content: str,
        content_hash: str | None = None,
    ) -> QualityResult:
        """
        Run all quality checks.

        Args:
            url: The URL.
            content: The text/markdown content.
            content_hash: Optional pre-computed content hash.

        Returns:
            QualityResult from first failing check, or passed.
        """
        # URL check first (fast)
        url_result = self.check_url(url)
        if not url_result.passed:
            return url_result

        # Content check
        content_result = self.check_content(content, url, content_hash)
        return content_result

    def clear_hash_cache(self) -> None:
        """Clear the content hash cache."""
        self._content_hashes.clear()

"""Tests for quality gate filtering."""

from ragcrawl.filters.quality_gates import QualityGate, QualityIssue


def test_block_patterns_and_invalid_pattern_handling() -> None:
    """Block patterns are applied and invalid regex is ignored."""
    gate = QualityGate(block_patterns=[r"forbidden", r"[invalid"])
    # Valid pattern blocks
    result = gate.check_url("https://example.com/forbidden/page")
    assert not result.passed
    assert result.issue is QualityIssue.BLOCKED_PATTERN
    # Invalid pattern should not block other URLs
    assert gate.check_url("https://example.com/ok").passed


def test_content_length_and_word_count_checks() -> None:
    """Fail when content is too short or has too few words."""
    gate = QualityGate(min_text_length=10, min_word_count=3)
    short = gate.check_content("tiny")
    assert not short.passed and short.issue is QualityIssue.TOO_SHORT

    gate.min_text_length = 1  # allow next check to run
    few_words = gate.check_content("one two", content_hash="hash1")
    assert not few_words.passed and few_words.issue is QualityIssue.LOW_WORD_COUNT


def test_duplicate_detection_and_cache_clear() -> None:
    """Detect duplicate content using provided content hash."""
    gate = QualityGate(min_text_length=1, min_word_count=1)
    first = gate.check_content("a" * 200, url="https://example.com/1", content_hash="h1")
    assert first.passed

    dup = gate.check_content("a" * 200, url="https://example.com/2", content_hash="h1")
    assert not dup.passed and dup.issue is QualityIssue.DUPLICATE_CONTENT
    assert dup.metrics["original_url"] == "https://example.com/1"

    gate.clear_hash_cache()
    # After clearing, same hash should pass again
    assert gate.check_content("a" * 200, url="https://example.com/3", content_hash="h1").passed


def test_language_detection_rejection() -> None:
    """Reject content when detected language not allowed."""
    gate = QualityGate(detect_language=True, allowed_languages=["fr"], min_text_length=1, min_word_count=1)
    result = gate.check_content("This content is clearly in English with the and is words.")
    assert not result.passed
    assert result.issue is QualityIssue.WRONG_LANGUAGE
    assert result.metrics["detected_language"] == "en"


def test_check_all_runs_url_then_content() -> None:
    """End-to-end check_all covers URL blocking and content acceptance."""
    gate = QualityGate(block_patterns=[r"/blocked"], min_text_length=10, min_word_count=2)
    blocked = gate.check_all("https://example.com/blocked", "ignored content")
    assert not blocked.passed and blocked.issue is QualityIssue.BLOCKED_PATTERN

    ok = gate.check_all("https://example.com/ok", "valid content with enough words", "hash2")
    assert ok.passed and ok.issue is QualityIssue.PASSED
    assert ok.metrics["text_length"] > 0 and ok.metrics["word_count"] > 0

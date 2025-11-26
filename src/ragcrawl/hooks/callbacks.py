"""Callback definitions and hook manager."""

import re
from typing import Any, Callable, Protocol

from ragcrawl.models.document import Document
from ragcrawl.models.page import Page
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


class OnPageCallback(Protocol):
    """Protocol for on_page callbacks."""

    def __call__(self, document: Document) -> None:
        """Called when a page is successfully crawled."""
        ...


class OnErrorCallback(Protocol):
    """Protocol for on_error callbacks."""

    def __call__(self, url: str, error: Exception) -> None:
        """Called when an error occurs during crawling."""
        ...


class OnChangeCallback(Protocol):
    """Protocol for on_change_detected callbacks."""

    def __call__(self, document: Document, previous_page: Page | None) -> None:
        """Called when content change is detected."""
        ...


class RedactionHook(Protocol):
    """Protocol for redaction hooks."""

    def __call__(self, content: str) -> str:
        """Redact sensitive content before persistence."""
        ...


class HookManager:
    """
    Manages hooks/callbacks for crawl events.
    """

    def __init__(self) -> None:
        """Initialize hook manager."""
        self._on_page_hooks: list[OnPageCallback] = []
        self._on_error_hooks: list[OnErrorCallback] = []
        self._on_change_hooks: list[OnChangeCallback] = []
        self._redaction_hook: RedactionHook | None = None

    def register_on_page(self, callback: OnPageCallback) -> None:
        """Register an on_page callback."""
        self._on_page_hooks.append(callback)

    def register_on_error(self, callback: OnErrorCallback) -> None:
        """Register an on_error callback."""
        self._on_error_hooks.append(callback)

    def register_on_change(self, callback: OnChangeCallback) -> None:
        """Register an on_change_detected callback."""
        self._on_change_hooks.append(callback)

    def set_redaction_hook(self, hook: RedactionHook) -> None:
        """Set the redaction hook."""
        self._redaction_hook = hook

    def trigger_on_page(self, document: Document) -> None:
        """Trigger on_page hooks."""
        for hook in self._on_page_hooks:
            try:
                hook(document)
            except Exception as e:
                logger.warning("on_page hook error", error=str(e))

    def trigger_on_error(self, url: str, error: Exception) -> None:
        """Trigger on_error hooks."""
        for hook in self._on_error_hooks:
            try:
                hook(url, error)
            except Exception as e:
                logger.warning("on_error hook error", error=str(e))

    def trigger_on_change(
        self, document: Document, previous_page: Page | None
    ) -> None:
        """Trigger on_change_detected hooks."""
        for hook in self._on_change_hooks:
            try:
                hook(document, previous_page)
            except Exception as e:
                logger.warning("on_change hook error", error=str(e))

    def apply_redaction(self, content: str) -> str:
        """Apply redaction hook to content."""
        if self._redaction_hook is None:
            return content

        try:
            return self._redaction_hook(content)
        except Exception as e:
            logger.warning("Redaction hook error", error=str(e))
            return content


# Built-in redaction patterns
class PatternRedactor:
    """
    Redacts content based on regex patterns.
    """

    def __init__(
        self,
        patterns: list[tuple[str, str]] | None = None,
        redact_emails: bool = True,
        redact_phone_numbers: bool = True,
        redact_ssn: bool = True,
        redact_credit_cards: bool = True,
    ) -> None:
        """
        Initialize pattern redactor.

        Args:
            patterns: List of (pattern, replacement) tuples.
            redact_emails: Redact email addresses.
            redact_phone_numbers: Redact phone numbers.
            redact_ssn: Redact SSN patterns.
            redact_credit_cards: Redact credit card numbers.
        """
        self.patterns: list[tuple[re.Pattern[str], str]] = []

        # Add custom patterns
        if patterns:
            for pattern, replacement in patterns:
                try:
                    self.patterns.append((re.compile(pattern), replacement))
                except re.error:
                    pass

        # Add built-in patterns
        if redact_emails:
            self.patterns.append((
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "[EMAIL REDACTED]",
            ))

        if redact_phone_numbers:
            self.patterns.append((
                re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
                "[PHONE REDACTED]",
            ))

        if redact_ssn:
            self.patterns.append((
                re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
                "[SSN REDACTED]",
            ))

        if redact_credit_cards:
            self.patterns.append((
                re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
                "[CARD REDACTED]",
            ))

    def __call__(self, content: str) -> str:
        """Apply redaction patterns to content."""
        result = content
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)
        return result

"""Pattern matching for URL filtering."""

import fnmatch
import re
from typing import Pattern


class PatternMatcher:
    """
    Matches URLs against include/exclude patterns.

    Supports both regex and glob patterns.
    """

    def __init__(
        self,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        """
        Initialize the pattern matcher.

        Args:
            include_patterns: Patterns for URLs to include (regex or glob).
            exclude_patterns: Patterns for URLs to exclude (regex or glob).
            case_sensitive: Whether pattern matching is case-sensitive.
        """
        self.case_sensitive = case_sensitive
        self._include_patterns = self._compile_patterns(include_patterns or [])
        self._exclude_patterns = self._compile_patterns(exclude_patterns or [])

    def _compile_patterns(self, patterns: list[str]) -> list[Pattern[str]]:
        """
        Compile patterns to regex.

        Args:
            patterns: List of pattern strings (regex or glob).

        Returns:
            List of compiled regex patterns.
        """
        compiled = []
        flags = 0 if self.case_sensitive else re.IGNORECASE

        for pattern in patterns:
            try:
                if self._is_glob_pattern(pattern):
                    # Convert glob to regex
                    regex = fnmatch.translate(pattern)
                    compiled.append(re.compile(regex, flags))
                else:
                    # Treat as regex
                    compiled.append(re.compile(pattern, flags))
            except re.error:
                # Invalid regex, try as literal
                escaped = re.escape(pattern)
                compiled.append(re.compile(escaped, flags))

        return compiled

    def _is_glob_pattern(self, pattern: str) -> bool:
        """
        Determine if a pattern is glob-style.

        Args:
            pattern: The pattern string.

        Returns:
            True if it looks like a glob pattern.
        """
        # Glob patterns typically use * and ? for wildcards
        # Regex patterns often use . and other special chars
        glob_chars = {"*", "?", "[", "]"}
        regex_chars = {"^", "$", "+", "|", "(", ")", "{", "}"}

        has_glob = any(c in pattern for c in glob_chars)
        has_regex = any(c in pattern for c in regex_chars)

        # If it has regex-specific chars, treat as regex
        if has_regex and not pattern.startswith("*"):
            return False

        # If it has glob chars but no regex chars, treat as glob
        return has_glob

    def matches_include(self, url: str) -> bool:
        """
        Check if URL matches any include pattern.

        Args:
            url: The URL to check.

        Returns:
            True if URL matches an include pattern or no include patterns defined.
        """
        if not self._include_patterns:
            return True

        return any(p.search(url) for p in self._include_patterns)

    def matches_exclude(self, url: str) -> bool:
        """
        Check if URL matches any exclude pattern.

        Args:
            url: The URL to check.

        Returns:
            True if URL matches an exclude pattern.
        """
        if not self._exclude_patterns:
            return False

        return any(p.search(url) for p in self._exclude_patterns)

    def should_include(self, url: str) -> bool:
        """
        Determine if URL should be included based on patterns.

        Exclude patterns take precedence over include patterns.

        Args:
            url: The URL to check.

        Returns:
            True if URL should be included.
        """
        # Exclude takes precedence
        if self.matches_exclude(url):
            return False

        return self.matches_include(url)

    def get_match_reason(self, url: str) -> str | None:
        """
        Get the reason for inclusion/exclusion.

        Args:
            url: The URL to check.

        Returns:
            A string describing the match, or None if included by default.
        """
        for pattern in self._exclude_patterns:
            if pattern.search(url):
                return f"excluded by pattern: {pattern.pattern}"

        if self._include_patterns:
            for pattern in self._include_patterns:
                if pattern.search(url):
                    return f"included by pattern: {pattern.pattern}"

            return "no include pattern matched"

        return None


class ExtensionFilter:
    """Filter URLs by file extension."""

    def __init__(self, blocked_extensions: list[str] | None = None) -> None:
        """
        Initialize extension filter.

        Args:
            blocked_extensions: List of extensions to block (e.g., ['.pdf', '.zip']).
        """
        self.blocked_extensions = set(
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (blocked_extensions or [])
        )

    def is_blocked(self, url: str) -> bool:
        """
        Check if URL has a blocked extension.

        Args:
            url: The URL to check.

        Returns:
            True if the URL has a blocked extension.
        """
        if not self.blocked_extensions:
            return False

        # Extract path from URL
        from urllib.parse import urlparse

        try:
            path = urlparse(url).path.lower()
        except Exception:
            return False

        # Check extension
        for ext in self.blocked_extensions:
            if path.endswith(ext):
                return True

        return False

    def get_extension(self, url: str) -> str | None:
        """
        Get the extension from a URL.

        Args:
            url: The URL.

        Returns:
            The extension (e.g., '.html') or None.
        """
        from urllib.parse import urlparse

        try:
            path = urlparse(url).path
            if "." in path:
                ext = "." + path.rsplit(".", 1)[-1].lower()
                # Filter out paths that look like directories
                if "/" not in ext and len(ext) <= 10:
                    return ext
        except Exception:
            pass

        return None

"""URL normalization for deterministic deduplication."""

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import tldextract
from yarl import URL


class URLNormalizer:
    """
    Normalizes URLs for deterministic deduplication.

    Handles:
    - Fragment removal
    - Trailing slash normalization
    - Query parameter sorting and filtering
    - Scheme normalization
    - Case normalization for hostname
    - Path normalization
    """

    def __init__(
        self,
        remove_fragments: bool = True,
        normalize_trailing_slash: bool = True,
        sort_query_params: bool = True,
        remove_query_params: list[str] | None = None,
        lowercase_hostname: bool = True,
        remove_default_ports: bool = True,
        remove_www: bool = False,
    ) -> None:
        """
        Initialize the URL normalizer.

        Args:
            remove_fragments: Remove URL fragments (#...).
            normalize_trailing_slash: Ensure consistent trailing slash handling.
            sort_query_params: Sort query parameters alphabetically.
            remove_query_params: List of query params to remove (e.g., tracking params).
            lowercase_hostname: Lowercase the hostname.
            remove_default_ports: Remove default ports (80, 443).
            remove_www: Remove www. prefix from hostname.
        """
        self.remove_fragments = remove_fragments
        self.normalize_trailing_slash = normalize_trailing_slash
        self.sort_query_params = sort_query_params
        self.remove_query_params = set(remove_query_params or [])
        self.lowercase_hostname = lowercase_hostname
        self.remove_default_ports = remove_default_ports
        self.remove_www = remove_www

        # Default tracking params to remove
        self.default_tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
            "source",
        }

    def normalize(self, url: str) -> str:
        """
        Normalize a URL for deduplication.

        Args:
            url: The URL to normalize.

        Returns:
            The normalized URL string.
        """
        try:
            parsed = urlparse(url)
        except Exception:
            return url

        # Scheme normalization (lowercase)
        scheme = parsed.scheme.lower()

        # Hostname normalization
        hostname = parsed.netloc
        if self.lowercase_hostname:
            hostname = hostname.lower()

        # Remove default ports
        if self.remove_default_ports:
            if scheme == "http" and hostname.endswith(":80"):
                hostname = hostname[:-3]
            elif scheme == "https" and hostname.endswith(":443"):
                hostname = hostname[:-4]

        # Remove www prefix
        if self.remove_www and hostname.startswith("www."):
            hostname = hostname[4:]

        # Path normalization
        path = parsed.path

        # Remove duplicate slashes
        path = re.sub(r"/+", "/", path)

        # Normalize path encoding
        # Decode safe characters that don't need encoding
        path = path.replace("%7E", "~")

        # Handle trailing slash
        if self.normalize_trailing_slash:
            # Keep trailing slash only for directories (no extension)
            if path and not path.endswith("/"):
                # Check if it looks like a file (has extension)
                last_segment = path.split("/")[-1]
                if "." not in last_segment and path != "/":
                    # It's a directory-like path, could add trailing slash
                    # But for consistency, we'll remove trailing slashes
                    pass
            # Remove trailing slash except for root
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")

        # Empty path becomes /
        if not path:
            path = "/"

        # Query parameter normalization
        query = parsed.query
        if query:
            params = parse_qs(query, keep_blank_values=True)

            # Remove tracking and specified params
            params_to_remove = self.remove_query_params | self.default_tracking_params
            params = {k: v for k, v in params.items() if k not in params_to_remove}

            # Sort and rebuild query string
            if self.sort_query_params:
                sorted_params = sorted(params.items())
                # Flatten multi-value params
                flat_params = []
                for k, values in sorted_params:
                    for v in sorted(values):
                        flat_params.append((k, v))
                query = urlencode(flat_params)
            else:
                query = urlencode(params, doseq=True)
        else:
            query = ""

        # Fragment handling
        fragment = "" if self.remove_fragments else parsed.fragment

        # Rebuild URL
        normalized = urlunparse((scheme, hostname, path, "", query, fragment))

        return normalized

    def get_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.

        Args:
            url: The URL.

        Returns:
            The domain (e.g., 'example.com').
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc.lower()

            # Remove port
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            return hostname
        except Exception:
            return ""

    def get_registered_domain(self, url: str) -> str:
        """
        Extract the registered domain (eTLD+1) from a URL.

        Args:
            url: The URL.

        Returns:
            The registered domain (e.g., 'example.com' for 'sub.example.com').
        """
        try:
            extracted = tldextract.extract(url)
            if extracted.domain and extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}"
            return extracted.domain or ""
        except Exception:
            return ""

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are on the same domain.

        Args:
            url1: First URL.
            url2: Second URL.

        Returns:
            True if same domain.
        """
        return self.get_domain(url1) == self.get_domain(url2)

    def is_same_registered_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are on the same registered domain.

        This considers subdomains as the same domain.

        Args:
            url1: First URL.
            url2: Second URL.

        Returns:
            True if same registered domain.
        """
        return self.get_registered_domain(url1) == self.get_registered_domain(url2)


# Default normalizer instance
_default_normalizer = URLNormalizer()


def normalize_url(url: str) -> str:
    """
    Normalize a URL using default settings.

    Args:
        url: The URL to normalize.

    Returns:
        The normalized URL.
    """
    return _default_normalizer.normalize(url)


def get_domain(url: str) -> str:
    """
    Get the domain from a URL.

    Args:
        url: The URL.

    Returns:
        The domain.
    """
    return _default_normalizer.get_domain(url)


def get_registered_domain(url: str) -> str:
    """
    Get the registered domain from a URL.

    Args:
        url: The URL.

    Returns:
        The registered domain.
    """
    return _default_normalizer.get_registered_domain(url)

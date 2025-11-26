"""Robots.txt parsing and checking."""

import asyncio
from urllib.parse import urljoin, urlparse

import httpx
from robotexclusionrulesparser import RobotExclusionRulesParser

from ragcrawl.config.crawler_config import RobotsMode
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """
    Checks URL access against robots.txt rules.
    """

    def __init__(
        self,
        mode: RobotsMode = RobotsMode.STRICT,
        user_agent: str = "ragcrawl",
        allowlist: list[str] | None = None,
        cache_ttl_seconds: int = 3600,
    ) -> None:
        """
        Initialize robots checker.

        Args:
            mode: Robots.txt compliance mode.
            user_agent: User agent to check rules for.
            allowlist: Domains to bypass robots.txt (when mode=ALLOWLIST).
            cache_ttl_seconds: How long to cache robots.txt files.
        """
        self.mode = mode
        self.user_agent = user_agent
        self.allowlist = set(d.lower() for d in (allowlist or []))
        self.cache_ttl_seconds = cache_ttl_seconds

        # Cache: domain -> (parser, timestamp)
        self._cache: dict[str, tuple[RobotExclusionRulesParser | None, float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.

        Args:
            url: The URL to check.

        Returns:
            True if crawling is allowed.
        """
        if self.mode == RobotsMode.OFF:
            return True

        domain = self._get_domain(url)

        if self.mode == RobotsMode.ALLOWLIST:
            if domain in self.allowlist:
                return True

        if self.mode == RobotsMode.OFF:
            return True

        # Get or fetch robots.txt
        parser = await self._get_parser(url)

        if parser is None:
            # If we can't fetch robots.txt, allow by default
            return True

        return parser.is_allowed(self.user_agent, url)

    async def _get_parser(self, url: str) -> RobotExclusionRulesParser | None:
        """
        Get or fetch robots.txt parser for a URL's domain.

        Args:
            url: URL to get parser for.

        Returns:
            Parser instance or None if unavailable.
        """
        domain = self._get_domain(url)
        robots_url = self._get_robots_url(url)

        async with self._lock:
            # Check cache
            if domain in self._cache:
                parser, timestamp = self._cache[domain]
                import time

                if time.time() - timestamp < self.cache_ttl_seconds:
                    return parser

            # Fetch robots.txt
            parser = await self._fetch_robots(robots_url)
            import time

            self._cache[domain] = (parser, time.time())
            return parser

    async def _fetch_robots(self, robots_url: str) -> RobotExclusionRulesParser | None:
        """
        Fetch and parse robots.txt.

        Args:
            robots_url: URL of robots.txt file.

        Returns:
            Parser instance or None if fetch failed.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    robots_url,
                    follow_redirects=True,
                    headers={"User-Agent": self.user_agent},
                )

                if response.status_code == 200:
                    parser = RobotExclusionRulesParser()
                    parser.parse(response.text)
                    logger.debug("Fetched robots.txt", url=robots_url)
                    return parser

                elif response.status_code == 404:
                    # No robots.txt means everything is allowed
                    logger.debug("No robots.txt found", url=robots_url)
                    return None

                else:
                    logger.warning(
                        "Failed to fetch robots.txt",
                        url=robots_url,
                        status=response.status_code,
                    )
                    return None

        except Exception as e:
            logger.warning("Error fetching robots.txt", url=robots_url, error=str(e))
            return None

    def get_crawl_delay(self, url: str) -> float | None:
        """
        Get crawl delay from robots.txt.

        Args:
            url: URL to check.

        Returns:
            Crawl delay in seconds, or None if not specified.
        """
        domain = self._get_domain(url)

        if domain in self._cache:
            parser, _ = self._cache[domain]
            if parser:
                delay = parser.get_crawl_delay(self.user_agent)
                if delay:
                    return float(delay)

        return None

    def get_sitemaps(self, url: str) -> list[str]:
        """
        Get sitemap URLs from robots.txt.

        Args:
            url: URL to check.

        Returns:
            List of sitemap URLs.
        """
        domain = self._get_domain(url)

        if domain in self._cache:
            parser, _ = self._cache[domain]
            if parser and hasattr(parser, "sitemaps"):
                return list(parser.sitemaps)

        return []

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def clear_cache(self) -> None:
        """Clear the robots.txt cache."""
        self._cache.clear()

"""Sitemap parsing for change prioritization."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx

from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SitemapEntry:
    """Entry from a sitemap."""

    loc: str
    lastmod: datetime | None = None
    changefreq: str | None = None
    priority: float | None = None


class SitemapParser:
    """
    Parses XML sitemaps for URL discovery and change prioritization.

    Supports:
    - Standard sitemap.xml
    - Sitemap index files
    - lastmod for change detection
    """

    # XML namespaces
    SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

    def __init__(
        self,
        user_agent: str = "ragcrawl/0.1",
        timeout: int = 30,
    ) -> None:
        """
        Initialize sitemap parser.

        Args:
            user_agent: User agent for fetching sitemaps.
            timeout: Request timeout in seconds.
        """
        self.user_agent = user_agent
        self.timeout = timeout

    async def parse(self, sitemap_url: str) -> list[SitemapEntry]:
        """
        Parse a sitemap URL.

        Handles both regular sitemaps and sitemap indexes.

        Args:
            sitemap_url: URL of the sitemap.

        Returns:
            List of sitemap entries.
        """
        try:
            content = await self._fetch(sitemap_url)
            if not content:
                return []

            # Check if it's a sitemap index
            if "<sitemapindex" in content:
                return await self._parse_sitemap_index(content, sitemap_url)
            else:
                return self._parse_sitemap(content)

        except Exception as e:
            logger.error("Failed to parse sitemap", url=sitemap_url, error=str(e))
            return []

    async def discover_sitemaps(self, base_url: str) -> list[str]:
        """
        Discover sitemap URLs for a site.

        Checks common locations:
        - /sitemap.xml
        - /sitemap_index.xml
        - robots.txt Sitemap directives

        Args:
            base_url: Base URL of the site.

        Returns:
            List of discovered sitemap URLs.
        """
        sitemaps = []

        # Try common locations
        common_paths = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml",
            "/sitemaps.xml",
        ]

        for path in common_paths:
            sitemap_url = urljoin(base_url, path)
            if await self._exists(sitemap_url):
                sitemaps.append(sitemap_url)
                break  # Usually only one is needed

        # Check robots.txt
        robots_url = urljoin(base_url, "/robots.txt")
        robots_sitemaps = await self._parse_robots_sitemaps(robots_url)
        sitemaps.extend(s for s in robots_sitemaps if s not in sitemaps)

        return sitemaps

    async def _fetch(self, url: str) -> str | None:
        """Fetch URL content."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )

                if response.status_code == 200:
                    return response.text

                return None

        except Exception as e:
            logger.debug("Failed to fetch", url=url, error=str(e))
            return None

    async def _exists(self, url: str) -> bool:
        """Check if URL exists."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.head(
                    url,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                return response.status_code == 200

        except Exception:
            return False

    def _parse_sitemap(self, content: str) -> list[SitemapEntry]:
        """Parse a regular sitemap."""
        entries = []

        try:
            root = ET.fromstring(content)

            for url_elem in root.findall(f"{self.SITEMAP_NS}url"):
                entry = self._parse_url_element(url_elem)
                if entry:
                    entries.append(entry)

            # Also try without namespace (some sitemaps don't use it)
            if not entries:
                for url_elem in root.findall("url"):
                    entry = self._parse_url_element(url_elem, namespace="")
                    if entry:
                        entries.append(entry)

        except ET.ParseError as e:
            logger.warning("XML parse error", error=str(e))

        return entries

    async def _parse_sitemap_index(
        self, content: str, base_url: str
    ) -> list[SitemapEntry]:
        """Parse a sitemap index and fetch all referenced sitemaps."""
        all_entries = []

        try:
            root = ET.fromstring(content)

            # Find all sitemap references
            sitemap_urls = []
            for sitemap_elem in root.findall(f"{self.SITEMAP_NS}sitemap"):
                loc_elem = sitemap_elem.find(f"{self.SITEMAP_NS}loc")
                if loc_elem is not None and loc_elem.text:
                    sitemap_urls.append(loc_elem.text.strip())

            # Also try without namespace
            if not sitemap_urls:
                for sitemap_elem in root.findall("sitemap"):
                    loc_elem = sitemap_elem.find("loc")
                    if loc_elem is not None and loc_elem.text:
                        sitemap_urls.append(loc_elem.text.strip())

            # Fetch each sitemap
            for sitemap_url in sitemap_urls:
                content = await self._fetch(sitemap_url)
                if content:
                    entries = self._parse_sitemap(content)
                    all_entries.extend(entries)

        except ET.ParseError as e:
            logger.warning("XML parse error in sitemap index", error=str(e))

        return all_entries

    def _parse_url_element(
        self, elem: ET.Element, namespace: str | None = None
    ) -> SitemapEntry | None:
        """Parse a URL element from sitemap."""
        ns = namespace if namespace is not None else self.SITEMAP_NS

        loc_elem = elem.find(f"{ns}loc")
        if loc_elem is None or not loc_elem.text:
            return None

        loc = loc_elem.text.strip()

        # Parse lastmod
        lastmod = None
        lastmod_elem = elem.find(f"{ns}lastmod")
        if lastmod_elem is not None and lastmod_elem.text:
            lastmod = self._parse_datetime(lastmod_elem.text.strip())

        # Parse changefreq
        changefreq = None
        changefreq_elem = elem.find(f"{ns}changefreq")
        if changefreq_elem is not None and changefreq_elem.text:
            changefreq = changefreq_elem.text.strip()

        # Parse priority
        priority = None
        priority_elem = elem.find(f"{ns}priority")
        if priority_elem is not None and priority_elem.text:
            try:
                priority = float(priority_elem.text.strip())
            except ValueError:
                pass

        return SitemapEntry(
            loc=loc,
            lastmod=lastmod,
            changefreq=changefreq,
            priority=priority,
        )

    def _parse_datetime(self, date_str: str) -> datetime | None:
        """Parse various datetime formats from sitemaps."""
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]

        # Handle timezone offset format
        date_str = date_str.replace("+00:00", "Z")

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    async def _parse_robots_sitemaps(self, robots_url: str) -> list[str]:
        """Extract sitemap URLs from robots.txt."""
        sitemaps = []

        content = await self._fetch(robots_url)
        if not content:
            return sitemaps

        for line in content.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                sitemap_url = line[8:].strip()
                if sitemap_url:
                    sitemaps.append(sitemap_url)

        return sitemaps

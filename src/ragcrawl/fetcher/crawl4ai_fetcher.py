"""Crawl4AI-based fetcher implementation."""

import asyncio
import contextlib
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from ragcrawl.config.crawler_config import FetchMode, RetryConfig
from ragcrawl.config.markdown_config import ContentFilterType, MarkdownConfig
from ragcrawl.fetcher.base import BaseFetcher, FetchResult, FetchStatus
from ragcrawl.fetcher.revalidation import Revalidator
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


class Crawl4AIFetcher(BaseFetcher):
    """
    Fetcher implementation using Crawl4AI.

    Supports HTTP-only, browser rendering, and hybrid modes.
    """

    def __init__(
        self,
        fetch_mode: FetchMode = FetchMode.HTTP,
        user_agent: str = "ragcrawl/0.1",
        timeout: int = 30,
        browser_timeout: int = 30000,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        proxy: str | None = None,
        retry_config: RetryConfig | None = None,
        follow_redirects: bool = True,
        max_redirects: int = 10,
        markdown_config: MarkdownConfig | None = None,
    ) -> None:
        """
        Initialize Crawl4AI fetcher.

        Args:
            fetch_mode: HTTP, browser, or hybrid mode.
            user_agent: User agent string.
            timeout: HTTP timeout in seconds.
            browser_timeout: Browser timeout in milliseconds.
            headers: Additional HTTP headers.
            cookies: Cookies to send.
            proxy: Proxy URL.
            retry_config: Retry configuration.
            follow_redirects: Whether to follow redirects.
            max_redirects: Maximum redirects to follow.
            markdown_config: Markdown generation and filtering configuration.
        """
        self.fetch_mode = fetch_mode
        self.user_agent = user_agent
        self.timeout = timeout
        self.browser_timeout = browser_timeout
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.proxy = proxy
        self.retry_config = retry_config or RetryConfig()
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self.markdown_config = markdown_config or MarkdownConfig()

        self.revalidator = Revalidator()
        self._crawler: Any = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure Crawl4AI is initialized (only for browser mode)."""
        if self._initialized:
            return

        # Only initialize Crawl4AI browser for BROWSER mode
        if self.fetch_mode == FetchMode.BROWSER:
            try:
                from crawl4ai import AsyncWebCrawler

                self._crawler = AsyncWebCrawler(verbose=False)
                await self._crawler.awarmup()
                logger.info("Crawl4AI browser initialized")
            except ImportError:
                logger.warning("Crawl4AI not available, browser mode disabled")
                self._crawler = None
            except Exception as e:
                logger.warning("Failed to initialize Crawl4AI browser", error=str(e))
                self._crawler = None

        self._initialized = True

    async def fetch(
        self,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> FetchResult:
        """
        Fetch a URL using Crawl4AI.

        Args:
            url: URL to fetch.
            etag: Optional ETag for conditional request.
            last_modified: Optional Last-Modified for conditional request.
            **kwargs: Additional options.

        Returns:
            FetchResult with content and metadata.
        """
        await self._ensure_initialized()

        start_time = time.time()
        fetch_started = datetime.now()

        try:
            # Try HTTP mode first if hybrid or HTTP
            if self.fetch_mode in (FetchMode.HTTP, FetchMode.HYBRID):
                result = await self._fetch_http(url, etag, last_modified)

                # If hybrid and content looks incomplete, try browser
                if (
                    self.fetch_mode == FetchMode.HYBRID
                    and result.is_success
                    and self._needs_browser_rendering(result)
                ):
                    logger.debug("Falling back to browser rendering", url=url)
                    result = await self._fetch_browser(url)
                    result.used_browser = True

            else:  # Browser mode
                result = await self._fetch_browser(url)
                result.used_browser = True

            # Set timing
            result.fetch_started_at = fetch_started
            result.fetch_completed_at = datetime.now()
            result.latency_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            logger.error("Fetch failed", url=url, error=str(e))
            return FetchResult(
                status=FetchStatus.ERROR,
                error=str(e),
                fetch_started_at=fetch_started,
                fetch_completed_at=datetime.now(),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def _fetch_http(
        self,
        url: str,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FetchResult:
        """Fetch using HTTP client."""
        import httpx

        headers = {**self.headers, "User-Agent": self.user_agent}

        # Add conditional headers
        cond_headers = self.revalidator.get_conditional_headers(etag, last_modified)
        headers.update(cond_headers)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=self.follow_redirects,
                max_redirects=self.max_redirects,
                proxy=self.proxy,
            ) as client:
                response = await client.get(url, headers=headers, cookies=self.cookies)

                # Handle 304 Not Modified
                if response.status_code == 304:
                    return FetchResult(
                        status=FetchStatus.NOT_MODIFIED,
                        status_code=304,
                        final_url=str(response.url),
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified"),
                        headers=dict(response.headers),
                    )

                # Handle redirects (final URL)
                final_url = str(response.url)

                # Get content
                html = response.text
                content_type = response.headers.get("content-type", "")

                # Extract using Crawl4AI if available
                markdown, title, description, links = await self._extract_content(
                    html, final_url
                )

                return FetchResult(
                    status=FetchStatus.SUCCESS,
                    status_code=response.status_code,
                    html=html,
                    markdown=markdown,
                    content_type=content_type,
                    content_length=len(html),
                    final_url=final_url,
                    etag=response.headers.get("etag"),
                    last_modified=response.headers.get("last-modified"),
                    headers=dict(response.headers),
                    title=title,
                    description=description,
                    links=links,
                )

        except httpx.TimeoutException:
            return FetchResult(
                status=FetchStatus.TIMEOUT,
                error="Request timed out",
            )
        except Exception as e:
            return FetchResult(
                status=FetchStatus.ERROR,
                error=str(e),
            )

    def _build_crawler_config(self) -> Any:
        """Build CrawlerRunConfig from markdown configuration."""
        from crawl4ai import CrawlerRunConfig
        from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

        mc = self.markdown_config

        # Build content filter based on configuration
        content_filter = None
        if mc.content_filter == ContentFilterType.PRUNING:
            try:
                from crawl4ai.content_filter_strategy import PruningContentFilter

                content_filter = PruningContentFilter(
                    threshold=mc.pruning_threshold,
                    threshold_type=mc.pruning_threshold_type,
                    min_word_threshold=mc.pruning_min_word_threshold,
                )
            except ImportError:
                logger.warning("PruningContentFilter not available, using no filter")
        elif mc.content_filter == ContentFilterType.BM25:
            if mc.user_query:
                try:
                    from crawl4ai.content_filter_strategy import BM25ContentFilter

                    content_filter = BM25ContentFilter(
                        user_query=mc.user_query,
                        bm25_threshold=mc.bm25_threshold,
                    )
                except ImportError:
                    logger.warning("BM25ContentFilter not available, using no filter")
            else:
                logger.warning("BM25 filter requires user_query, using no filter")

        # Build markdown generator with options
        markdown_generator_options = {
            "ignore_links": mc.ignore_links,
            "ignore_images": mc.ignore_images,
            "escape_html": mc.escape_html,
            "body_width": mc.body_width,
            "skip_internal_links": mc.skip_internal_links,
            "include_sup_sub": mc.include_sup_sub,
        }

        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter,
            options=markdown_generator_options,
        )

        # Build CrawlerRunConfig with all options
        config_kwargs: dict[str, Any] = {
            "markdown_generator": markdown_generator,
            "word_count_threshold": mc.word_count_threshold,
            "remove_overlay_elements": mc.remove_overlay_elements,
            "process_iframes": mc.process_iframes,
            "excluded_tags": mc.excluded_tags,
            "remove_forms": mc.remove_forms,
            "exclude_external_links": mc.exclude_external_links,
            "exclude_social_media_links": mc.exclude_social_media_links,
            "exclude_external_images": mc.exclude_external_images,
        }

        # Add optional parameters only if set
        if mc.excluded_selector:
            config_kwargs["excluded_selector"] = mc.excluded_selector
        if mc.css_selector:
            config_kwargs["css_selector"] = mc.css_selector
        if mc.target_elements:
            config_kwargs["target_elements"] = mc.target_elements
        if mc.exclude_domains:
            config_kwargs["exclude_domains"] = mc.exclude_domains

        return CrawlerRunConfig(**config_kwargs)

    def _extract_markdown_from_result(self, result: Any) -> str:
        """Extract the appropriate markdown from Crawl4AI result."""
        mc = self.markdown_config

        # Handle MarkdownGenerationResult object (Crawl4AI 0.5+)
        markdown_obj = result.markdown
        if markdown_obj is None:
            return ""

        # If it's a string (older Crawl4AI), return as-is
        if isinstance(markdown_obj, str):
            return markdown_obj

        # For MarkdownGenerationResult, choose the appropriate output
        if mc.include_citations and hasattr(markdown_obj, "markdown_with_citations"):
            md = markdown_obj.markdown_with_citations
            if md:
                return md

        if mc.use_fit_markdown and hasattr(markdown_obj, "fit_markdown"):
            fit_md = markdown_obj.fit_markdown
            if fit_md:
                return fit_md

        # Fall back to raw_markdown
        if hasattr(markdown_obj, "raw_markdown"):
            return markdown_obj.raw_markdown or ""

        # Last resort: convert to string
        return str(markdown_obj) if markdown_obj else ""

    async def _fetch_browser(self, url: str) -> FetchResult:
        """Fetch using browser rendering via Crawl4AI."""
        if self._crawler is None:
            # Fallback to HTTP if Crawl4AI not available
            return await self._fetch_http(url)

        try:
            config = self._build_crawler_config()
            result = await self._crawler.arun(url=url, config=config)

            if not result.success:
                return FetchResult(
                    status=FetchStatus.ERROR,
                    error=result.error_message or "Crawl4AI fetch failed",
                )

            # Extract markdown using the new helper
            markdown = self._extract_markdown_from_result(result)

            # Extract links
            links = []
            if result.links:
                internal = result.links.get("internal", [])
                external = result.links.get("external", [])
                links = [
                    link.get("href", "")
                    for link in internal + external
                    if link.get("href")
                ]

            return FetchResult(
                status=FetchStatus.SUCCESS,
                status_code=result.status_code,
                html=result.html,
                markdown=markdown,
                content_type="text/html",
                content_length=len(result.html) if result.html else 0,
                final_url=result.url,
                title=result.metadata.get("title") if result.metadata else None,
                description=(
                    result.metadata.get("description") if result.metadata else None
                ),
                links=links,
                used_browser=True,
            )

        except Exception as e:
            logger.error("Browser fetch failed", url=url, error=str(e))
            return FetchResult(
                status=FetchStatus.ERROR,
                error=str(e),
            )

    async def _extract_content(
        self, html: str, url: str
    ) -> tuple[str, str | None, str | None, list[str]]:
        """
        Extract markdown, title, description, and links from HTML.

        Uses Crawl4AI with configured markdown generator and content filters
        for high-quality LLM-ready output.

        Args:
            html: HTML content.
            url: Page URL.

        Returns:
            Tuple of (markdown, title, description, links).
        """
        if self._crawler is not None:
            try:
                # Build config with markdown generator and filters
                config = self._build_crawler_config()

                # Process raw HTML
                result = await self._crawler.arun(
                    url=url,
                    config=config,
                    raw_html=html,
                )

                if result.success:
                    # Extract markdown using configured options
                    markdown = self._extract_markdown_from_result(result)

                    links = []
                    if result.links:
                        internal = result.links.get("internal", [])
                        external = result.links.get("external", [])
                        links = [
                            link.get("href", "")
                            for link in internal + external
                            if link.get("href")
                        ]

                    return (
                        markdown,
                        result.metadata.get("title") if result.metadata else None,
                        result.metadata.get("description") if result.metadata else None,
                        links,
                    )

            except Exception as e:
                logger.debug("Crawl4AI extraction failed, using fallback", error=str(e))

        # Fallback extraction
        return self._fallback_extract(html, url)

    def _fallback_extract(
        self, html: str, url: str
    ) -> tuple[str, str | None, str | None, list[str]]:
        """Fallback HTML extraction without Crawl4AI."""
        import re

        # Simple title extraction
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else None

        # Simple description extraction
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        description = desc_match.group(1).strip() if desc_match else None

        # Simple link extraction
        links = re.findall(r'href=["\']([^"\']+)["\']', html)
        # Filter and normalize links
        normalized_links = []
        for link in links:
            if link.startswith(("http://", "https://", "/")):
                if link.startswith("/"):
                    link = urljoin(url, link)
                normalized_links.append(link)

        # Simple HTML to text (very basic)
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        markdown = text.strip()

        return markdown, title, description, normalized_links

    def _needs_browser_rendering(self, result: FetchResult) -> bool:
        """
        Determine if content needs browser rendering.

        Checks for signs that JavaScript rendering is needed.
        """
        if not result.markdown:
            return True

        # Check for common SPA indicators
        html = result.html or ""
        spa_indicators = [
            "ng-app",
            "data-reactroot",
            "__NEXT_DATA__",
            "window.__NUXT__",
            "id=\"app\"",
            "id=\"root\"",
        ]

        for indicator in spa_indicators:
            if indicator in html and len(result.markdown) < 500:
                return True

        return False

    async def fetch_batch(
        self,
        urls: list[str],
        **kwargs: Any,
    ) -> list[FetchResult]:
        """Fetch multiple URLs concurrently."""
        tasks = [self.fetch(url, **kwargs) for url in urls]
        return await asyncio.gather(*tasks)

    async def close(self) -> None:
        """Close Crawl4AI resources."""
        if self._crawler is not None:
            with contextlib.suppress(Exception):
                await self._crawler.aclose()
            self._crawler = None
            self._initialized = False

    def health_check(self) -> bool:
        """Check if fetcher is ready."""
        return True  # HTTP always available

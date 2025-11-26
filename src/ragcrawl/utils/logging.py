"""Structured logging setup for ragcrawl."""

import logging
import sys
from typing import Any

import structlog


def setup_logging(
    level: int = logging.INFO,
    json_format: bool = False,
    log_file: str | None = None,
) -> None:
    """
    Set up structured logging for the crawler.

    Args:
        level: Logging level (default: INFO).
        json_format: If True, output logs as JSON.
        log_file: Optional file path to write logs to.
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Configure structlog processors
    shared_processors: list[structlog.typing.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically module name).
        **initial_context: Initial context to bind to the logger.

    Returns:
        A structlog BoundLogger instance.
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class CrawlLoggerAdapter:
    """
    Adapter for logging crawl events with consistent context.
    """

    def __init__(self, run_id: str, site_id: str) -> None:
        """
        Initialize the logger adapter.

        Args:
            run_id: Current crawl run ID.
            site_id: Site being crawled.
        """
        self.logger = get_logger(
            "ragcrawl",
            run_id=run_id,
            site_id=site_id,
        )

    def page_discovered(self, url: str, depth: int, referrer: str | None = None) -> None:
        """Log page discovery."""
        self.logger.debug(
            "Page discovered",
            url=url,
            depth=depth,
            referrer=referrer,
        )

    def page_fetched(
        self,
        url: str,
        status_code: int,
        latency_ms: float,
        size_bytes: int | None = None,
    ) -> None:
        """Log page fetch completion."""
        self.logger.info(
            "Page fetched",
            url=url,
            status_code=status_code,
            latency_ms=round(latency_ms, 2),
            size_bytes=size_bytes,
        )

    def page_extracted(
        self,
        url: str,
        markdown_size: int,
        links_found: int,
        latency_ms: float,
    ) -> None:
        """Log content extraction."""
        self.logger.debug(
            "Content extracted",
            url=url,
            markdown_size=markdown_size,
            links_found=links_found,
            latency_ms=round(latency_ms, 2),
        )

    def page_skipped(self, url: str, reason: str) -> None:
        """Log page skip."""
        self.logger.debug("Page skipped", url=url, reason=reason)

    def page_failed(self, url: str, error: str, retry_count: int = 0) -> None:
        """Log page failure."""
        self.logger.warning(
            "Page failed",
            url=url,
            error=error,
            retry_count=retry_count,
        )

    def content_changed(self, url: str, old_hash: str | None, new_hash: str) -> None:
        """Log content change detection."""
        self.logger.info(
            "Content changed",
            url=url,
            old_hash=old_hash,
            new_hash=new_hash,
        )

    def tombstone_created(self, url: str, status_code: int) -> None:
        """Log tombstone creation for deleted page."""
        self.logger.info(
            "Tombstone created",
            url=url,
            status_code=status_code,
        )

    def run_started(self, seeds: list[str], config_summary: dict[str, Any]) -> None:
        """Log crawl run start."""
        self.logger.info(
            "Crawl run started",
            seeds=seeds,
            config=config_summary,
        )

    def run_completed(self, stats: dict[str, Any], duration_seconds: float) -> None:
        """Log crawl run completion."""
        self.logger.info(
            "Crawl run completed",
            stats=stats,
            duration_seconds=round(duration_seconds, 2),
        )

    def run_failed(self, error: str) -> None:
        """Log crawl run failure."""
        self.logger.error("Crawl run failed", error=error)

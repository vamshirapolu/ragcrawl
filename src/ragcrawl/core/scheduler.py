"""Domain-based scheduling and rate limiting."""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ragcrawl.config.crawler_config import RateLimitConfig
from ragcrawl.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainState:
    """State for a single domain."""

    last_request_time: float = 0.0
    request_count: int = 0
    active_requests: int = 0
    error_count: int = 0
    consecutive_errors: int = 0
    circuit_open: bool = False
    circuit_open_until: float = 0.0


class DomainScheduler:
    """
    Manages per-domain rate limiting and scheduling.

    Features:
    - Per-domain request rate limiting
    - Per-domain concurrency limits
    - Circuit breaker for failing domains
    - Global rate limiting
    """

    def __init__(
        self,
        config: RateLimitConfig,
        max_concurrency: int = 10,
    ) -> None:
        """
        Initialize the scheduler.

        Args:
            config: Rate limit configuration.
            max_concurrency: Global max concurrent requests.
        """
        self.config = config
        self.max_concurrency = max_concurrency

        # Per-domain state
        self._domain_states: dict[str, DomainState] = defaultdict(DomainState)

        # Global state
        self._last_global_request = 0.0
        self._active_requests = 0

        # Semaphores
        self._global_semaphore = asyncio.Semaphore(max_concurrency)
        self._domain_semaphores: dict[str, asyncio.Semaphore] = {}

        # Circuit breaker config
        self._error_threshold = 5  # Consecutive errors to open circuit
        self._circuit_timeout = 60.0  # Seconds to keep circuit open

    async def acquire(self, domain: str) -> bool:
        """
        Acquire permission to make a request to a domain.

        Args:
            domain: Target domain.

        Returns:
            True if request can proceed, False if blocked.
        """
        # Check circuit breaker
        state = self._domain_states[domain]
        if state.circuit_open:
            if time.time() < state.circuit_open_until:
                logger.debug("Circuit open for domain", domain=domain)
                return False
            else:
                # Half-open: allow one request
                state.circuit_open = False

        # Global rate limit
        await self._wait_global_rate()

        # Domain rate limit
        await self._wait_domain_rate(domain)

        # Acquire semaphores
        await self._global_semaphore.acquire()

        domain_sem = self._get_domain_semaphore(domain)
        await domain_sem.acquire()

        # Update state
        state.active_requests += 1
        state.request_count += 1
        state.last_request_time = time.time()
        self._active_requests += 1
        self._last_global_request = time.time()

        return True

    def release(self, domain: str, success: bool = True) -> None:
        """
        Release a request slot.

        Args:
            domain: Target domain.
            success: Whether the request succeeded.
        """
        state = self._domain_states[domain]
        state.active_requests = max(0, state.active_requests - 1)
        self._active_requests = max(0, self._active_requests - 1)

        # Update circuit breaker
        if success:
            state.consecutive_errors = 0
        else:
            state.error_count += 1
            state.consecutive_errors += 1

            if state.consecutive_errors >= self._error_threshold:
                state.circuit_open = True
                state.circuit_open_until = time.time() + self._circuit_timeout
                logger.warning(
                    "Circuit opened for domain",
                    domain=domain,
                    consecutive_errors=state.consecutive_errors,
                )

        # Release semaphores
        self._global_semaphore.release()

        domain_sem = self._get_domain_semaphore(domain)
        domain_sem.release()

    async def _wait_global_rate(self) -> None:
        """Wait for global rate limit."""
        if self.config.requests_per_second <= 0:
            return

        min_interval = 1.0 / self.config.requests_per_second
        elapsed = time.time() - self._last_global_request

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

    async def _wait_domain_rate(self, domain: str) -> None:
        """Wait for domain-specific rate limit."""
        if not self.config.per_domain_rps:
            return

        state = self._domain_states[domain]
        min_interval = 1.0 / self.config.per_domain_rps
        elapsed = time.time() - state.last_request_time

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        # Additional delay if configured
        if self.config.delay_between_requests > 0:
            await asyncio.sleep(self.config.delay_between_requests)

    def _get_domain_semaphore(self, domain: str) -> asyncio.Semaphore:
        """Get or create domain semaphore."""
        if domain not in self._domain_semaphores:
            self._domain_semaphores[domain] = asyncio.Semaphore(
                self.config.per_domain_concurrency
            )
        return self._domain_semaphores[domain]

    def set_crawl_delay(self, domain: str, delay: float) -> None:
        """
        Set custom crawl delay for a domain (from robots.txt).

        Args:
            domain: Target domain.
            delay: Delay in seconds.
        """
        # Store as effective per-domain rate
        # This will be used in _wait_domain_rate
        # For now, just log it
        logger.debug("Crawl delay set", domain=domain, delay=delay)

    def get_domain_stats(self, domain: str) -> dict[str, Any]:
        """Get statistics for a domain."""
        state = self._domain_states[domain]
        return {
            "request_count": state.request_count,
            "error_count": state.error_count,
            "active_requests": state.active_requests,
            "circuit_open": state.circuit_open,
            "consecutive_errors": state.consecutive_errors,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get overall scheduler statistics."""
        return {
            "active_requests": self._active_requests,
            "domains_tracked": len(self._domain_states),
            "circuits_open": sum(
                1 for s in self._domain_states.values() if s.circuit_open
            ),
        }

    @property
    def active_requests(self) -> int:
        """Number of active requests."""
        return self._active_requests

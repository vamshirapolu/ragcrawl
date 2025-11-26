"""Sync strategy orchestration."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ragcrawl.config.sync_config import SyncStrategy


@dataclass
class StrategyResult:
    """Result from a sync strategy."""

    strategy: SyncStrategy
    should_fetch: bool
    reason: str
    metadata: dict[str, Any] | None = None


class SyncStrategyOrchestrator:
    """
    Orchestrates multiple sync strategies.

    Tries strategies in order until one provides a definitive answer.
    """

    def __init__(
        self,
        strategies: list[SyncStrategy],
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            strategies: Strategies to use, in order of preference.
        """
        self.strategies = strategies

    def get_strategy_order(self) -> list[SyncStrategy]:
        """Get the order of strategies to try."""
        return self.strategies

    def should_try_strategy(self, strategy: SyncStrategy) -> bool:
        """Check if a strategy should be tried."""
        return strategy in self.strategies

    def get_next_strategy(
        self,
        current: SyncStrategy | None,
    ) -> SyncStrategy | None:
        """Get the next strategy to try after current."""
        if current is None:
            return self.strategies[0] if self.strategies else None

        try:
            idx = self.strategies.index(current)
            if idx + 1 < len(self.strategies):
                return self.strategies[idx + 1]
        except ValueError:
            pass

        return None

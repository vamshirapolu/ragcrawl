"""Hooks and callbacks for ragcrawl."""

from ragcrawl.hooks.callbacks import (
    HookManager,
    OnChangeCallback,
    OnErrorCallback,
    OnPageCallback,
    RedactionHook,
)

__all__ = [
    "HookManager",
    "OnPageCallback",
    "OnErrorCallback",
    "OnChangeCallback",
    "RedactionHook",
]

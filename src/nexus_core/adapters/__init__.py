"""Domain adapter registry — maps domains onto the frozen core vocabulary."""

from __future__ import annotations

from nexus_core.adapters.base import DomainAdapter, FileDomainAdapter, get_adapter, list_adapters

__all__ = [
    "DomainAdapter",
    "FileDomainAdapter",
    "get_adapter",
    "list_adapters",
]

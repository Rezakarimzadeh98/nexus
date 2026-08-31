"""Stable adapter contract for Phase 11+.

Adapters never invent core types — they only declare domain metadata and
point at source YAML that the ingestion engine already understands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from nexus_core.ingestion.models import SourceConfig
from nexus_core.ingestion.registry import load_sources
from nexus_core.types import Observation

REPO_ROOT = Path(__file__).resolve().parents[3]


@runtime_checkable
class DomainAdapter(Protocol):
    """Public adapter surface (semver-stable for 1.x)."""

    @property
    def domain(self) -> str: ...

    @property
    def display_name(self) -> str: ...

    @property
    def description(self) -> str: ...

    def sources_path(self, *, offline: bool = False) -> Path: ...

    def load_source_configs(self, *, offline: bool = False) -> list[SourceConfig]: ...

    def annotate_observation(self, obs: Observation) -> Observation: ...

    def as_dict(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class FileDomainAdapter:
    """YAML-backed adapter living under ``adapters/<domain>/``."""

    domain: str
    display_name: str
    description: str
    non_goals: tuple[str, ...] = ()
    root: Path = field(default=REPO_ROOT)

    def _dir(self) -> Path:
        return self.root / "adapters" / self.domain

    def sources_path(self, *, offline: bool = False) -> Path:
        name = "sources.ci.yaml" if offline else "sources.yaml"
        path = self._dir() / name
        if not path.is_file():
            raise FileNotFoundError(f"missing adapter sources: {path}")
        return path

    def load_source_configs(self, *, offline: bool = False) -> list[SourceConfig]:
        return load_sources(self.sources_path(offline=offline))

    def annotate_observation(self, obs: Observation) -> Observation:
        meta = dict(obs.metadata)
        meta.setdefault("domain", self.domain)
        return obs.model_copy(update={"metadata": meta})

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "display_name": self.display_name,
            "description": self.description,
            "non_goals": list(self.non_goals),
            "sources_live": str(self._dir() / "sources.yaml"),
            "sources_ci": str(self._dir() / "sources.ci.yaml"),
        }


_ADAPTERS: dict[str, FileDomainAdapter] = {
    "generic": FileDomainAdapter(
        domain="generic",
        display_name="Generic / multi-domain",
        description="Default public wedge: hazards, science, health, and cross-cutting news.",
    ),
    "finance": FileDomainAdapter(
        domain="finance",
        display_name="Finance (public)",
        description="Public market / regulatory disclosures mapped onto core observations.",
    ),
    "cyber": FileDomainAdapter(
        domain="cyber",
        display_name="Cyber (public vulns)",
        description="Public vulnerability and advisory feeds (NVD, CISA KEV).",
    ),
    "supply_chain": FileDomainAdapter(
        domain="supply_chain",
        display_name="Supply chain (public)",
        description="Public logistics / trade signals when ToS-safe feeds are available.",
    ),
    "defense": FileDomainAdapter(
        domain="defense",
        display_name="Defense analysis (open only)",
        description=(
            "Open-source analytical reporting only. Not an operational targeting system."
        ),
        non_goals=(
            "targeting",
            "weapons employment",
            "closed military datasets",
            "real-time battlespace C2",
        ),
    ),
}


def get_adapter(domain: str) -> FileDomainAdapter:
    key = domain.strip().lower()
    if key not in _ADAPTERS:
        known = ", ".join(sorted(_ADAPTERS))
        raise KeyError(f"unknown adapter '{domain}' (known: {known})")
    return _ADAPTERS[key]


def list_adapters() -> list[FileDomainAdapter]:
    return [_ADAPTERS[k] for k in sorted(_ADAPTERS)]

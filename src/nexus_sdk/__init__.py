"""NEXUS Python SDK — thin HTTP client over the public API."""

from __future__ import annotations

from typing import Any, cast

import httpx

from nexus_core import __version__ as _core_version

__version__ = _core_version


class NexusClient:
    """Synchronous client for NEXUS read + authenticated write routes."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        headers: dict[str, str] = {"User-Agent": f"nexus-sdk/{__version__}"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> NexusClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._client.get("/health").raise_for_status().json())

    def live(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._client.get("/live").raise_for_status().json())

    def signals(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self._client.get("/signals", params={"limit": limit}).raise_for_status().json(),
        )

    def signal(self, signal_id: str) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self._client.get(f"/signals/{signal_id}").raise_for_status().json(),
        )

    def forecasts(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return cast(
            list[dict[str, Any]],
            self._client.get("/forecasts", params={"limit": limit}).raise_for_status().json(),
        )

    def evaluation(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._client.get("/evaluation").raise_for_status().json())

    def learning(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._client.get("/learning").raise_for_status().json())

    def adapters(self) -> list[dict[str, Any]]:
        res = self._client.get("/v1/adapters").raise_for_status().json()
        return cast(list[dict[str, Any]], res)

    def run_ingest(
        self,
        *,
        adapter: str = "generic",
        offline: bool = True,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        payload = {"adapter": adapter, "offline": offline, "dry_run": dry_run}
        return cast(
            dict[str, Any],
            self._client.post("/v1/jobs/ingest", json=payload).raise_for_status().json(),
        )

    def run_detect(
        self,
        *,
        limit: int = 500,
        velocity_threshold: float = 1.5,
        min_short_volume: float = 2.0,
    ) -> dict[str, Any]:
        payload = {
            "limit": limit,
            "velocity_threshold": velocity_threshold,
            "min_short_volume": min_short_volume,
        }
        return cast(
            dict[str, Any],
            self._client.post("/v1/jobs/detect", json=payload).raise_for_status().json(),
        )

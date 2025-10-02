from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Iterable, List, Optional, Protocol

log = logging.getLogger(__name__)


class MetricsProvider(Protocol):
    """Protocol for metrics data providers."""

    def iter_docs(self) -> Iterable[tuple[str, dict]]:
        """Iterate over metrics documents."""
        ...

    def describe(self) -> dict:
        """Describe the provider configuration."""
        ...


class JsonMetricsProvider:
    """JSON file-based metrics provider."""

    def __init__(self, paths: List[Path]) -> None:
        self.paths = paths

    def iter_docs(self) -> Iterable[tuple[str, dict]]:
        """Iterate over JSON files in paths."""
        for p in self.paths:
            if p.is_dir():
                for f in sorted(p.rglob("*.json")):
                    yield str(f), json.loads(f.read_text(encoding="utf-8"))
            elif p.is_file() and p.suffix == ".json":
                yield str(p), json.loads(p.read_text(encoding="utf-8"))

    def describe(self) -> dict:
        return {"kind": "json", "paths": [str(p) for p in self.paths]}


class BenchAPIClient:
    """Bench API client for metrics (stub implementation)."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        token: Optional[str],
        params: dict | None = None,
        timeout: float = 10.0,
        page_size: int = 500,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.project_id = project_id
        self.token = token or os.getenv("BENCH_API_TOKEN")
        self.params = params or {}
        self.timeout = timeout
        self.page_size = page_size

    def iter_docs(self) -> Iterable[tuple[str, dict]]:
        """Iterate over API documents."""
        if os.getenv("BENCH_API_OFFLINE") == "1":
            log.warning("BenchAPIClient offline; no docs yielded")
            return

        try:
            import requests
        except ImportError:
            log.error("requests not available for BenchAPIClient")
            return

        page = 1
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        while True:
            try:
                r = requests.get(
                    f"{self.base_url}/projects/{self.project_id}/metrics",
                    params={**self.params, "page": page, "page_size": self.page_size},
                    headers=headers,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                log.error("bench api error page=%s: %s", page, e)
                break

            items = data.get("items") or []
            for it in items:
                sid = it.get("id") or f"api:{page}:{len(items)}"
                yield str(sid), it

            if not data.get("next_page"):
                break
            page += 1

    def describe(self) -> dict:
        return {
            "kind": "bench_api",
            "base_url": self.base_url,
            "project_id": self.project_id,
        }


class HistoricalMetricsCache:
    """Cache for historical metrics data."""

    def __init__(self, inner: MetricsProvider | None, path: Path, mode: str = "rw") -> None:
        self.inner = inner
        self.path = path
        self.mode = mode

    def iter_docs(self) -> Iterable[tuple[str, dict]]:
        """Iterate over cached documents."""
        if self.mode in ("read", "rw") and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                yield rec["source_id"], rec["obj"]
            return

        if self.mode in ("write", "rw") and self.inner is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                for source_id, obj in self.inner.iter_docs():
                    f.write(
                        json.dumps({"source_id": source_id, "obj": obj}, ensure_ascii=False) + "\n"
                    )
                    yield source_id, obj
            return

        log.warning(
            "HistoricalMetricsCache: no data (mode=%s, exists=%s)",
            self.mode,
            self.path.exists(),
        )

    def describe(self) -> dict:
        return {
            "kind": "cache",
            "path": str(self.path),
            "mode": self.mode,
            "has_cache": self.path.exists(),
        }


class CompositeProvider:
    """Composite provider that combines multiple providers."""

    def __init__(self, providers: List[MetricsProvider]) -> None:
        self.providers = providers

    def iter_docs(self) -> Iterable[tuple[str, dict]]:
        """Iterate over all provider documents."""
        for p in self.providers:
            yield from p.iter_docs()

    def describe(self) -> dict:
        return {
            "kind": "composite",
            "children": [p.describe() for p in self.providers],
        }

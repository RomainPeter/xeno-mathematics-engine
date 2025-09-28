from __future__ import annotations
from typing import Protocol, Iterable, Dict, Any
from pathlib import Path
import json


class MetricsProvider(Protocol):
    """Protocol for metrics data providers."""

    def load(self) -> Iterable[Dict[str, Any]]:
        """Load metrics data."""
        ...


class JsonMetricsProvider:
    """JSON file-based metrics provider."""

    def __init__(self, sources: list[Path]) -> None:
        self.sources = sources

    def load(self) -> Iterable[Dict[str, Any]]:
        """Load JSON metrics from sources."""
        for p in self.sources:
            if p.is_dir():
                for f in sorted(p.rglob("*.json")):
                    yield json.loads(f.read_text(encoding="utf-8"))
            elif p.is_file() and p.suffix == ".json":
                yield json.loads(p.read_text(encoding="utf-8"))

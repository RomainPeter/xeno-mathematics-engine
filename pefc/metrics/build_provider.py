from __future__ import annotations
from pathlib import Path

from pefc.metrics.providers import (
    JsonMetricsProvider,
    BenchAPIClient,
    HistoricalMetricsCache,
    CompositeProvider,
    MetricsProvider,
)


def build_provider(cfg) -> MetricsProvider:
    """Build metrics provider from configuration."""
    # Check if provider is configured
    if not hasattr(cfg.metrics, "provider") or cfg.metrics.provider is None:
        # défaut: json avec metrics.sources si présents
        paths = [Path(p) for p in (getattr(cfg.metrics, "sources", []) or [])]
        return JsonMetricsProvider(paths)

    k = cfg.metrics.provider.kind
    if k == "json":
        paths = [Path(p) for p in cfg.metrics.provider.json.paths]
        return JsonMetricsProvider(paths)
    if k == "bench_api":
        p = cfg.metrics.provider.bench_api
        return BenchAPIClient(
            base_url=p.base_url,
            project_id=p.project_id,
            token=None,
            params=p.params,
        )
    if k == "cache":
        p = cfg.metrics.provider.cache
        inner = None
        if hasattr(cfg.metrics.provider, "inner") and cfg.metrics.provider.inner:
            inner = build_provider(cfg.metrics.provider.inner)  # optionnel
        return HistoricalMetricsCache(inner=inner, path=Path(p.path), mode=p.mode)
    if k == "composite":
        subs = [build_provider(sub) for sub in cfg.metrics.provider.composite.providers]
        return CompositeProvider(subs)

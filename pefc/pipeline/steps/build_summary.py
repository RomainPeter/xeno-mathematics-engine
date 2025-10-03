from __future__ import annotations

import logging
from pathlib import Path

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.summary import build_summary

log = logging.getLogger(__name__)


class BuildSummary(PackStep):
    """Build summary.json from metrics provider."""

    def run(self, ctx: PipelineContext) -> None:
        """Build summary.json using metrics provider."""
        log.info("build_summary: generating summary.json")

        # Get provider from context
        provider = ctx.meta.get("provider")
        if not provider:
            raise ValueError("no provider in context, run CollectSeeds first")

        # Build summary
        summary_path = ctx.work_dir / "summary.json"
        result = build_summary(
            sources=[],  # Empty sources when using provider
            out_path=summary_path,
            include_aggregates=ctx.cfg.metrics.include_aggregates,
            weight_key=ctx.cfg.metrics.weight_key,
            dedup=ctx.cfg.metrics.dedup,
            version=ctx.cfg.pack.version,
            prefer_backend=(ctx.cfg.metrics.backend if ctx.cfg.metrics.backend != "auto" else None),
            bounded_metrics=getattr(ctx.cfg.metrics, "bounded_metrics", []),
            schema_path=(
                Path(ctx.cfg.metrics.schema_path)
                if getattr(ctx.cfg.metrics, "schema_path", None)
                else None
            ),
            provider=provider,
        )

        # Add to context
        ctx.add_file("summary.json", summary_path)

        # Log results
        log.info("build_summary: generated summary with %d runs", result["overall"]["n_runs"])
        if result["overall"]["metrics"]:
            log.info("build_summary: metrics: %s", list(result["overall"]["metrics"].keys()))

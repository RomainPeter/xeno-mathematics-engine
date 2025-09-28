from __future__ import annotations
import logging

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.metrics.build_provider import build_provider

log = logging.getLogger(__name__)


class CollectSeeds(PackStep):
    """Collect metrics seeds and build provider."""

    def run(self, ctx: PipelineContext) -> None:
        """Build metrics provider from configuration."""
        log.info("collect_seeds: building metrics provider")

        # Build provider from config
        try:
            provider = build_provider(ctx.cfg)
            ctx.add_meta("provider", provider)

            # Log provider description
            desc = provider.describe()
            log.info("collect_seeds: using provider %s", desc)
        except Exception as e:
            log.error("collect_seeds: failed to build provider: %s", e)
            raise

        # Optionally copy seed files if patterns specified
        patterns = self.config.get("patterns", [])
        for pattern in patterns:
            # Simple glob pattern matching
            matches = list(ctx.work_dir.glob(pattern))
            for match in matches:
                if match.is_file():
                    arcname = match.name
                    ctx.add_file(arcname, match)
                    log.debug("collect_seeds: added seed file %s", arcname)

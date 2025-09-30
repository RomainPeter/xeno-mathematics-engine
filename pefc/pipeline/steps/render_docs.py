from __future__ import annotations
import logging

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.onepager.render import build_onepager

log = logging.getLogger(__name__)


class RenderDocs(PackStep):
    """Render documentation (one-pager)."""

    def run(self, ctx: PipelineContext) -> None:
        """Generate one-pager markdown."""
        log.info("render_docs: generating one-pager")

        # Generate one-pager
        onepager_path = build_onepager(ctx.cfg, ctx.work_dir)

        # Add to context
        ctx.add_file("ONEPAGER.md", onepager_path)

        log.info("render_docs: generated one-pager at %s", onepager_path)

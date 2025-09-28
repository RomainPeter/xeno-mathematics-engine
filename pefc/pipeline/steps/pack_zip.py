from __future__ import annotations
from pathlib import Path
import zipfile
import logging

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.errors import PackBuildError

log = logging.getLogger(__name__)


class PackZip(PackStep):
    """Pack files into zip archive."""

    def run(self, ctx: PipelineContext) -> None:
        """Create zip archive with deduplication."""
        log.info("pack_zip: creating zip archive")

        # Determine output path
        out_path = self.config.get(
            "out", f"dist/{ctx.cfg.pack.pack_name}-{ctx.cfg.pack.version}.zip"
        )
        if not Path(out_path).is_absolute():
            out_path = ctx.out_dir / out_path

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Create zip with deduplication
        seen = set()
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for arcname, src_path in ctx.files.items():
                if arcname in seen:
                    raise PackBuildError(f"duplicate arcname: {arcname}")

                if not src_path.exists():
                    log.warning("pack_zip: file not found %s", src_path)
                    continue

                zf.write(src_path, arcname)
                seen.add(arcname)
                log.debug("pack_zip: added %s -> %s", src_path, arcname)

        # Log final file list
        log.info(
            "pack_zip: created %s with %d files: %s", out_path, len(seen), sorted(seen)
        )

        # Add zip to context
        ctx.add_file(out_path.name, out_path)

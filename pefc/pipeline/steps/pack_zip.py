from __future__ import annotations
from pathlib import Path
import zipfile
import logging
import json

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.errors import PackBuildError
from pefc.pack.merkle import build_entries, compute_merkle_root, build_manifest

log = logging.getLogger(__name__)


class PackZip(PackStep):
    """Pack files into zip archive."""

    def run(self, ctx: PipelineContext) -> None:
        """Create zip archive with deduplication."""
        log.info("pack_zip: creating zip archive")

        # Determine output path
        out_path = self.config.get(
            "out", f"{ctx.cfg.pack.pack_name}-{ctx.cfg.pack.version}.zip"
        )
        if not Path(out_path).is_absolute():
            out_path = ctx.out_dir / out_path

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate T18 manifest first
        log.info("pack_zip: generating T18 manifest")

        # Build entries for manifest (excluding manifest.json and merkle.txt from Merkle calculation)
        entries = []
        for arcname, src_path in ctx.files.items():
            if src_path.exists() and arcname not in {"manifest.json", "merkle.txt"}:
                entries.append((src_path, arcname))

        # Compute Merkle root (excluding manifest.json and merkle.txt)
        merkle_entries = build_entries(entries)
        merkle_root = compute_merkle_root(merkle_entries)

        # Build manifest with T18 format
        manifest = build_manifest(
            entries=merkle_entries,
            merkle_root=merkle_root,
            pack_name=ctx.cfg.pack.pack_name,
            version=ctx.cfg.pack.version,
            cli_version=getattr(ctx.cfg, "cli_version", "0.1.0"),
            signature_info={"present": False} if not ctx.cfg.sign.enabled else None,
        )

        # Create zip with deduplication and T18 manifest
        seen = set()
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add payload files (excluding manifest.json and merkle.txt)
            for arcname, src_path in ctx.files.items():
                if arcname in seen:
                    raise PackBuildError(f"duplicate arcname: {arcname}")

                if not src_path.exists():
                    log.warning("pack_zip: file not found %s", src_path)
                    continue

                # Skip manifest.json and merkle.txt as we'll add them separately
                if arcname in {"manifest.json", "merkle.txt"}:
                    continue

                zf.write(src_path, arcname)
                seen.add(arcname)
                log.debug("pack_zip: added %s -> %s", src_path, arcname)

            # Add T18 manifest and merkle
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("merkle.txt", merkle_root + "\n")
            seen.add("manifest.json")
            seen.add("merkle.txt")
            log.info("pack_zip: added T18 manifest.json and merkle.txt to zip")

        # Log final file list
        log.info(
            "pack_zip: created %s with %d files: %s", out_path, len(seen), sorted(seen)
        )

        # Add zip to context
        ctx.add_file(out_path.name, out_path)

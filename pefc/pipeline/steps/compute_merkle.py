from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pefc.pipeline.core import PackStep, PipelineContext

log = logging.getLogger(__name__)


class ComputeMerkle(PackStep):
    """Compute Merkle root and manifest."""

    def run(self, ctx: PipelineContext) -> None:
        """Compute Merkle root and generate manifest.json."""
        log.info("compute_merkle: computing Merkle root")

        # Collect file entries
        entries = []
        for arcname, src_path in ctx.files.items():
            if not src_path.exists():
                log.warning("compute_merkle: file not found %s", src_path)
                continue

            # Compute SHA256
            file_hash = self._file_sha256(src_path)
            size = src_path.stat().st_size

            entries.append(
                {
                    "path": arcname,
                    "size": size,
                    "sha256": file_hash,
                }
            )

        # Sort by path for deterministic order
        entries.sort(key=lambda x: x["path"])

        # Compute Merkle root
        merkle_root = self._compute_merkle_root(entries)

        # Generate manifest
        manifest = {
            "version": "1",
            "algorithm": "sha256",
            "pack_version": ctx.cfg.pack.version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(entries),
            "merkle_root": merkle_root,
            "files": entries,
        }

        # Write manifest
        manifest_path = ctx.work_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )

        # Write merkle.txt
        merkle_path = ctx.work_dir / "merkle.txt"
        merkle_path.write_text(merkle_root + "\n", encoding="utf-8", newline="\n")

        # Add to context
        ctx.add_file("manifest.json", manifest_path)
        ctx.add_file("merkle.txt", merkle_path)

        log.info(
            "compute_merkle: computed root %s for %d files",
            merkle_root[:16] + "...",
            len(entries),
        )

    def _file_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):  # 1 MiB chunks
                h.update(chunk)
        return h.hexdigest()

    def _compute_merkle_root(self, entries: list) -> str:
        """Compute Merkle root from file entries."""
        h = hashlib.sha256()
        for entry in entries:
            h.update((entry["path"] + "\n").encode("utf-8"))
            h.update((entry["sha256"] + "\n").encode("utf-8"))
            h.update((str(entry["size"]) + "\n").encode("utf-8"))
        return h.hexdigest()

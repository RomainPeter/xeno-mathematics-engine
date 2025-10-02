from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

CANDIDATES = ["sbom.json", "bom.json", "sbom.spdx.json", "sbom.cdx.json"]


def find_sbom(out_dir: Path, explicit_path: str | None) -> tuple[dict | None, str | None]:
    """
    Find and load SBOM file.

    Args:
        out_dir: Output directory to search in
        explicit_path: Explicit path to SBOM file (optional)

    Returns:
        Tuple of (sbom_obj, reason_if_none)
        - If explicit_path: try to load; otherwise explicit reason
        - Otherwise: try candidates in out_dir; otherwise reason
    """
    if explicit_path:
        p = Path(explicit_path)
        if not p.is_absolute():
            p = (out_dir / explicit_path).resolve()
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")), None
            except Exception as e:
                return None, f"SBOM found but unreadable: {p.name} ({e})"
        return None, f"SBOM path not found: {p}"

    # auto-detect
    for name in CANDIDATES:
        p = out_dir / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")), None
            except Exception as e:
                return None, f"SBOM candidate unreadable: {name} ({e})"

    return None, "No SBOM file detected in out_dir"

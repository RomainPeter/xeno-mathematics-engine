from __future__ import annotations
from pathlib import Path
import json


def load_manifest(path: Path) -> dict:
    """
    Load and validate manifest.json file.

    Args:
        path: Path to manifest.json file

    Returns:
        Parsed manifest dictionary

    Raises:
        ValueError: If manifest is invalid or missing required keys
    """
    obj = json.loads(path.read_text(encoding="utf-8"))
    if "merkle_root" not in obj or "files" not in obj:
        raise ValueError("Invalid manifest.json: missing required keys")
    return obj

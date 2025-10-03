#!/usr/bin/env python3
"""Fail the build if merge conflict markers remain in tracked files.

This script scans content tracked by git (excluding selected generated
directories) and reports any lines that still contain merge conflict markers
such as <<<<<<<, =======, or >>>>>>>.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable

MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
EXCLUDE_PREFIXES = ("out/", "test_pack/")


def iter_tracked_files() -> Iterable[Path]:
    """Yield tracked file paths, skipping excluded directories."""

    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if not line:
            continue
        if line.endswith("/"):
            continue
        if any(line.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        yield Path(line)


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return a list of (line_number, line_content) with conflict markers."""

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # pragma: no cover - e.g., file removed between ls-files and read
        return []

    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if any(line.strip().startswith(marker) for marker in MARKERS):
            hits.append((lineno, line.strip()))
    return hits


def main() -> int:
    root = Path.cwd()
    problems: list[str] = []

    for path in iter_tracked_files():
        entries = scan_file(root / path)
        for lineno, line in entries:
            problems.append(f"{path}:{lineno}: {line}")

    if problems:
        print("Merge conflict markers detected:", file=sys.stderr)
        for entry in problems:
            print(f"  {entry}", file=sys.stderr)
        print("Resolve conflicts and re-run.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Tests for CollectSeeds-style input collection constraints.
Ensures only configured inputs are collected and empty config errors.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from pefc.pack.builder import build_pack


def _write(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_empty_inputs_config_raises():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cfg = tmp / "cfg.json"
        cfg.write_text(json.dumps({"inputs": {}}))
        out = tmp / "out"
        with pytest.raises(RuntimeError):
            build_pack(cfg, out, run_id="r1")


def test_collect_files_globs_dirs_only_from_config():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cwd = os.getcwd()
        os.chdir(tmp)
        # Workspace files
        _write(tmp / "a.txt", "A")
        _write(tmp / "b" / "b.txt", "B")
        _write(tmp / "c" / "ignore.txt", "X")

        # Config selects a file and a dir, plus a glob
        cfg = tmp / "cfg.json"
        cfg.write_text(
            json.dumps(
                {
                    "inputs": {
                        "files": ["a.txt"],
                        "globs": ["b/*.txt"],
                        "dirs": ["c"],
                    },
                    "allow_outside_workspace": False,
                }
            )
        )

        out = tmp / "out"
        try:
            res = build_pack(cfg, out, run_id="r2")
            run_dir = Path(res["run_dir"])
            # Inputs must be present under run_dir/inputs
            assert (run_dir / "inputs" / "a.txt").exists()
            assert (run_dir / "inputs" / "b" / "b.txt").exists()
            assert (run_dir / "inputs" / "c" / "ignore.txt").exists()
        finally:
            os.chdir(cwd)

"""
Tests pour la CLI AE demo avec l'algorithme réel.
"""

import subprocess
import sys
from pathlib import Path

import orjson


def test_cli_demo_uses_real_algo(tmp_path: Path):
    """Test que la CLI demo utilise l'algorithme réel."""
    out = tmp_path / "psp.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "ae",
            "demo",
            "--context",
            "tests/fixtures/fca/context_4x4.json",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    data = orjson.loads(out.read_bytes())
    assert len(data["blocks"]) >= 3
    assert "meta" in data
    assert data["meta"]["theorem"] == "AE Next-Closure"


def test_cli_demo_5x3_context(tmp_path: Path):
    """Test que la CLI demo fonctionne avec le contexte 5x3."""
    out = tmp_path / "psp_5x3.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "ae",
            "demo",
            "--context",
            "tests/fixtures/fca/context_5x3.json",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    data = orjson.loads(out.read_bytes())
    assert len(data["blocks"]) >= 5
    assert data["meta"]["theorem"] == "AE Next-Closure"

"""
Tests pour la démonstration AE qui produit un PSP valide.
"""

import subprocess
import sys
from pathlib import Path

import orjson


def test_ae_demo_outputs_valid_psp(tmp_path: Path):
    """Test que la commande AE demo produit un PSP valide."""
    out = tmp_path / "psp.json"
    ctx = "examples/fca/context_4x4.json"

    r = subprocess.run(
        [sys.executable, "-m", "xme.cli.main", "ae", "demo", "--context", ctx, "--out", str(out)],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    data = orjson.loads(out.read_bytes())
    assert "blocks" in data and "edges" in data
    assert len(data["blocks"]) >= 1

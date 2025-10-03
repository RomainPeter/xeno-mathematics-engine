"""
Tests pour la gestion des timeouts CEGIS.
"""

import subprocess
import sys
from pathlib import Path

from xme.pcap.store import PCAPStore


def test_cegis_timeout_incident(tmp_path: Path):
    """Test qu'un timeout CEGIS génère un incident."""
    # Créer un run PCAP
    store = PCAPStore.new_run(tmp_path)
    run_path = store.path

    # Exécuter CEGIS avec un budget très court
    result_path = tmp_path / "result.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "cegis",
            "demo",
            "--secret",
            "1111111111111111",  # Secret long pour forcer le timeout
            "--max-iters",
            "100",
            "--out",
            str(result_path),
            "--run",
            str(run_path),
            "--cegis-ms",
            "1",  # Budget très court
        ],
        capture_output=True,
        text=True,
    )

    # Le timeout peut causer un échec, mais pas de crash
    assert r.returncode in (0, 1)

    # Vérifier les logs PCAP
    entries = list(store.read_all())
    actions = [entry.get("action", "") for entry in entries if entry.get("type") == "action"]

    # Doit contenir l'incident de timeout
    assert "incident.cegis_timeout" in actions


def test_cegis_timeout_incident_obligations(tmp_path: Path):
    """Test que l'incident de timeout contient les bonnes obligations."""
    # Créer un run PCAP
    store = PCAPStore.new_run(tmp_path)
    run_path = store.path

    # Exécuter CEGIS avec un budget très court
    result_path = tmp_path / "result.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "cegis",
            "demo",
            "--secret",
            "1111111111111111",
            "--max-iters",
            "100",
            "--out",
            str(result_path),
            "--run",
            str(run_path),
            "--cegis-ms",
            "1",
        ],
        capture_output=True,
        text=True,
    )

    # Vérifier les logs PCAP
    entries = list(store.read_all())
    timeout_entries = [e for e in entries if e.get("action") == "incident.cegis_timeout"]

    if timeout_entries:
        timeout_entry = timeout_entries[0]
        assert "budget_ms" in timeout_entry["obligations"]
        assert timeout_entry["obligations"]["budget_ms"] == "1"

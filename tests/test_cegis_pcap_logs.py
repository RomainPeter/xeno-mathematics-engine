"""
Tests pour les logs PCAP de CEGIS.
"""
import subprocess
import sys
import orjson
from pathlib import Path
from xme.pcap.store import PCAPStore


def test_cegis_pcap_logs(tmp_path: Path):
    """Test que CEGIS génère les logs PCAP attendus."""
    # Créer un run PCAP
    store = PCAPStore.new_run(tmp_path)
    run_path = store.path
    
    # Exécuter CEGIS via CLI
    result_path = tmp_path / "result.json"
    r = subprocess.run([
        sys.executable, "-m", "xme.cli.main", "cegis", "demo",
        "--secret", "1010",
        "--max-iters", "4",
        "--out", str(result_path),
        "--run", str(run_path)
    ], capture_output=True, text=True)
    
    assert r.returncode == 0
    
    # Vérifier que le résultat est valide
    result_data = orjson.loads(result_path.read_bytes())
    assert result_data["ok"] is True
    assert result_data["candidate"]["bits"] == "1010"
    
    # Vérifier les logs PCAP
    entries = list(store.read_all())
    
    # Vérifier qu'il y a au moins un log propose et un verify
    actions = [entry.get("action", "") for entry in entries if entry.get("type") == "action"]
    
    assert "cegis_propose" in actions
    assert any("cegis_verify" in action for action in actions)
    assert "cegis_done" in actions


def test_cegis_pcap_logs_detailed(tmp_path: Path):
    """Test détaillé des logs PCAP CEGIS."""
    # Créer un run PCAP
    store = PCAPStore.new_run(tmp_path)
    run_path = store.path
    
    # Exécuter CEGIS via CLI
    result_path = tmp_path / "result.json"
    r = subprocess.run([
        sys.executable, "-m", "xme.cli.main", "cegis", "demo",
        "--secret", "1101",
        "--max-iters", "8",
        "--out", str(result_path),
        "--run", str(run_path)
    ], capture_output=True, text=True)
    
    assert r.returncode == 0
    
    # Vérifier les logs PCAP
    entries = list(store.read_all())
    action_entries = [e for e in entries if e.get("type") == "action"]
    
    # Vérifier la séquence des actions
    actions = [e["action"] for e in action_entries]
    
    # Doit commencer par cegis_start
    assert actions[0] == "cegis_start"
    
    # Doit contenir des propose/verify
    assert "cegis_propose" in actions
    assert any("cegis_verify" in action for action in actions)
    
    # Doit finir par cegis_done
    assert actions[-1] == "cegis_done"
    
    # Vérifier les obligations
    start_entry = next(e for e in action_entries if e["action"] == "cegis_start")
    assert "secret_length" in start_entry["obligations"]
    assert "max_iters" in start_entry["obligations"]
    
    done_entry = next(e for e in action_entries if e["action"] == "cegis_done")
    assert "result_ok" in done_entry["obligations"]
    assert "iterations" in done_entry["obligations"]

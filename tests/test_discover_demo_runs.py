"""
Tests pour l'exécution de la boucle discovery.
"""

import subprocess
import sys
from pathlib import Path

import orjson

from xme.pcap.store import PCAPStore


def test_discover_demo_runs(tmp_path: Path):
    """Test que discover demo exécute N tours sans erreur."""
    # Exécuter discover demo
    result_path = tmp_path / "discovery.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "discover",
            "demo",
            "--turns",
            "3",
            "--ae-context",
            "examples/fca/context_4x4.json",
            "--secret",
            "10110",
            "--out",
            str(result_path),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    assert "Discovery demo OK" in r.stdout

    # Vérifier que le fichier de résultat existe
    assert result_path.exists()

    # Vérifier le contenu du résultat
    result_data = orjson.loads(result_path.read_bytes())
    assert "config" in result_data
    assert "results" in result_data
    assert "final_stats" in result_data
    assert "best_arm" in result_data
    assert "total_reward" in result_data

    # Vérifier qu'il y a 3 tours
    assert len(result_data["results"]) == 3

    # Vérifier que chaque tour a les bonnes clés
    for turn_result in result_data["results"]:
        assert "turn" in turn_result
        assert "arm" in turn_result
        assert "reward" in turn_result
        assert turn_result["arm"] in ["ae", "cegis"]


def test_discover_demo_pcap_logs(tmp_path: Path):
    """Test que discover demo génère des logs PCAP."""
    # Créer un run PCAP
    store = PCAPStore.new_run(tmp_path)
    run_path = store.path

    # Exécuter discover demo
    result_path = tmp_path / "discovery.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "discover",
            "demo",
            "--turns",
            "3",
            "--ae-context",
            "examples/fca/context_4x4.json",
            "--secret",
            "10110",
            "--out",
            str(result_path),
            "--run",
            str(run_path),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0

    # Vérifier les logs PCAP
    entries = list(store.read_all())
    actions = [entry.get("action", "") for entry in entries if entry.get("type") == "action"]

    # Doit contenir les actions discovery
    assert "discovery_start" in actions
    assert "discovery_select" in actions
    assert "discovery_reward" in actions
    assert "discovery_done" in actions

    # Vérifier qu'il y a au moins 3 sélections (une par tour)
    select_actions = [a for a in actions if a == "discovery_select"]
    assert len(select_actions) >= 3


def test_discover_demo_output_files(tmp_path: Path):
    """Test que discover demo génère les fichiers de sortie."""
    # Exécuter discover demo
    result_path = tmp_path / "discovery.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "discover",
            "demo",
            "--turns",
            "3",
            "--ae-context",
            "examples/fca/context_4x4.json",
            "--secret",
            "10110",
            "--out",
            str(result_path),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0

    # Vérifier que des fichiers de sortie ont été créés
    output_dir = result_path.parent

    # Chercher les fichiers de sortie
    ae_files = list(output_dir.glob("ae_turn_*.json"))
    cegis_files = list(output_dir.glob("cegis_turn_*.json"))

    # Au moins un fichier doit être créé
    assert len(ae_files) + len(cegis_files) > 0

    # Vérifier le contenu des fichiers
    for ae_file in ae_files:
        if ae_file.exists():
            data = orjson.loads(ae_file.read_bytes())
            assert "blocks" in data
            assert "edges" in data

    for cegis_file in cegis_files:
        if cegis_file.exists():
            data = orjson.loads(cegis_file.read_bytes())
            assert "candidate" in data
            assert "iters" in data
            assert "ok" in data


def test_discover_demo_rewards(tmp_path: Path):
    """Test que discover demo génère des récompenses > 0."""
    # Exécuter discover demo
    result_path = tmp_path / "discovery.json"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "discover",
            "demo",
            "--turns",
            "5",
            "--ae-context",
            "examples/fca/context_4x4.json",
            "--secret",
            "10110",
            "--out",
            str(result_path),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0

    # Vérifier les récompenses
    result_data = orjson.loads(result_path.read_bytes())

    # Au moins une récompense doit être > 0
    rewards = [turn["reward"] for turn in result_data["results"]]
    assert max(rewards) > 0

    # La récompense totale doit être > 0
    assert result_data["total_reward"] > 0

    # Vérifier les statistiques finales
    final_stats = result_data["final_stats"]
    assert "ae" in final_stats
    assert "cegis" in final_stats

    # Au moins une arme doit avoir été utilisée
    total_count = final_stats["ae"]["count"] + final_stats["cegis"]["count"]
    assert total_count == 5  # 5 tours

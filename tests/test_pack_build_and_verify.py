"""
Tests pour la construction et vérification d'Audit Packs.
"""

import subprocess
import sys
from pathlib import Path

from xme.pefc.pack import build_manifest, collect_inputs, verify_pack, write_zip


def test_pack_build_and_verify(tmp_path: Path):
    """Test de construction et vérification d'un pack."""
    # Créer des fichiers factices
    psp_file = tmp_path / "test.psp.json"
    psp_file.write_text('{"blocks": [], "edges": [], "meta": {"theorem": "test"}}')

    pcap_file = tmp_path / "test.pcap.jsonl"
    pcap_file.write_text(
        '{"type": "action", "action": "test", "timestamp": "2024-01-01T00:00:00Z"}\n'
    )

    # Collecter les fichiers
    inputs = collect_inputs([str(tmp_path / "*.json"), str(tmp_path / "*.jsonl")], default=False)
    assert len(inputs) == 2

    # Construire le manifest
    manifest = build_manifest(inputs)
    assert len(manifest.files) == 2
    assert manifest.merkle_root != ""
    assert len(manifest.merkle_root) == 64  # SHA256 hex length

    # Écrire le pack
    pack_path = write_zip(manifest, str(tmp_path))
    assert pack_path.exists()

    # Vérifier le pack
    ok, reason = verify_pack(pack_path)
    assert ok
    assert reason == "ok"


def test_pack_manifest_structure(tmp_path: Path):
    """Test de la structure du manifest."""
    # Créer un fichier de test
    test_file = tmp_path / "test.json"
    test_file.write_text('{"test": "data"}')

    # Construire le manifest
    inputs = collect_inputs([str(test_file)], default=False)
    manifest = build_manifest(inputs)

    # Vérifier la structure
    assert manifest.version == 1
    assert manifest.tool == "xme"
    assert len(manifest.files) == 1
    assert manifest.files[0].path == str(test_file)
    assert manifest.files[0].size > 0
    assert len(manifest.files[0].sha256) == 64
    assert len(manifest.merkle_root) == 64


def test_cli_pack_build_and_verify(tmp_path: Path):
    """Test de la CLI pack build et verify."""
    # Créer des fichiers factices
    psp_file = tmp_path / "test.psp.json"
    psp_file.write_text('{"blocks": [], "edges": [], "meta": {"theorem": "test"}}')

    # Test build
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "xme.cli.main",
            "pack",
            "build",
            "--include",
            str(tmp_path / "*.json"),
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    assert "Pack built" in r.stdout

    # Trouver le pack créé
    pack_files = list(tmp_path.glob("pack-*.zip"))
    assert len(pack_files) == 1
    pack_path = pack_files[0]

    # Test verify
    r = subprocess.run(
        [sys.executable, "-m", "xme.cli.main", "pack", "verify", "--pack", str(pack_path)],
        capture_output=True,
        text=True,
    )

    assert r.returncode == 0
    assert "Pack verified" in r.stdout

"""
Tests pour la détection de tampering dans les Audit Packs.
"""

import zipfile
from pathlib import Path

from xme.pefc.pack import build_manifest, collect_inputs, verify_pack, write_zip


def test_pack_tamper_detection(tmp_path: Path):
    """Test de détection de tampering."""
    # Créer un fichier de test
    test_file = tmp_path / "test.psp.json"
    original_content = '{"blocks": [], "edges": [], "meta": {"theorem": "test"}}'
    test_file.write_text(original_content)

    # Construire le pack original
    inputs = collect_inputs([str(test_file)], default=False)
    manifest = build_manifest(inputs)
    pack_path = write_zip(manifest, str(tmp_path))

    # Vérifier que le pack original est valide
    ok, reason = verify_pack(pack_path)
    assert ok
    assert reason == "ok"

    # Tamper le pack : modifier un octet dans le ZIP
    with zipfile.ZipFile(pack_path, "r") as zf:
        with zf.open("test.psp.json") as f:
            content = f.read()

    # Modifier un octet
    tampered_content = bytearray(content)
    tampered_content[0] = (tampered_content[0] + 1) % 256

    # Réécrire le ZIP avec le contenu modifié
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Copier tous les fichiers sauf celui qu'on modifie
        with zipfile.ZipFile(pack_path, "r") as original_zf:
            for name in original_zf.namelist():
                if name != "test.psp.json":
                    zf.writestr(name, original_zf.read(name))

        # Ajouter le fichier modifié
        zf.writestr("test.psp.json", bytes(tampered_content))
        zf.writestr("manifest.json", manifest.model_dump_json())

    # Vérifier que le tampering est détecté
    ok, reason = verify_pack(pack_path)
    assert not ok
    assert "hash_mismatch" in reason


def test_pack_missing_file_detection(tmp_path: Path):
    """Test de détection de fichier manquant."""
    # Créer un fichier de test
    test_file = tmp_path / "test.psp.json"
    test_file.write_text('{"blocks": [], "edges": [], "meta": {"theorem": "test"}}')

    # Construire le pack
    inputs = collect_inputs([str(test_file)], default=False)
    manifest = build_manifest(inputs)
    pack_path = write_zip(manifest, str(tmp_path))

    # Vérifier que le pack original est valide
    ok, reason = verify_pack(pack_path)
    assert ok

    # Créer un pack avec un fichier manquant
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Ajouter seulement le manifest, pas les fichiers
        zf.writestr("manifest.json", manifest.model_dump_json())

    # Vérifier que le fichier manquant est détecté
    ok, reason = verify_pack(pack_path)
    assert not ok
    assert "missing_file" in reason


def test_pack_corrupted_manifest(tmp_path: Path):
    """Test de détection de manifest corrompu."""
    # Créer un fichier de test
    test_file = tmp_path / "test.psp.json"
    test_file.write_text('{"blocks": [], "edges": [], "meta": {"theorem": "test"}}')

    # Construire le pack
    inputs = collect_inputs([str(test_file)], default=False)
    manifest = build_manifest(inputs)
    pack_path = write_zip(manifest, str(tmp_path))

    # Corrompre le manifest
    with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", "invalid json content")
        zf.write(test_file, test_file.name)

    # Vérifier que la corruption est détectée
    ok, reason = verify_pack(pack_path)
    assert not ok
    assert "error" in reason

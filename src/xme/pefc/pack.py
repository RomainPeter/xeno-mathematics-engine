"""
Logique de collecte et construction de l'Audit Pack.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timezone
import zipfile
import glob
import hashlib
import orjson
from .manifest import Manifest, FileEntry, calc_file_sha256, build_merkle


def collect_inputs(include: List[str], default: bool = True) -> List[Tuple[Path, str]]:
    """
    Collecte les fichiers d'entrée selon les patterns glob.
    
    Args:
        include: Liste des patterns glob à inclure
        default: Si True, ajoute les patterns par défaut
    
    Returns:
        Liste des tuples (chemin, type) des fichiers collectés
    """
    inputs: List[Tuple[Path, str]] = []
    
    # Patterns par défaut si demandé
    if default:
        default_patterns = [
            "artifacts/psp/*.json",
            "artifacts/pcap/run-*.jsonl",
            "docs/psp.schema.json",
            "sbom/sbom.spdx.json"
        ]
        include = include + default_patterns
    
    # Collecter les fichiers
    for pattern in include:
        for file_path in glob.glob(pattern, recursive=True):
            path = Path(file_path)
            if path.exists() and path.is_file():
                # Déterminer le type basé sur le chemin
                if "psp" in str(path):
                    kind = "psp"
                elif "pcap" in str(path):
                    kind = "pcap"
                elif "schema" in str(path):
                    kind = "schema"
                elif "sbom" in str(path):
                    kind = "sbom"
                else:
                    kind = "other"
                
                inputs.append((path, kind))
    
    return inputs


def build_manifest(inputs: List[Tuple[Path, str]], run_path: Optional[str] = None) -> Manifest:
    """
    Construit le manifest à partir des fichiers collectés.
    
    Args:
        inputs: Liste des fichiers collectés
        run_path: Chemin du run PCAP (optionnel)
    
    Returns:
        Manifest construit
    """
    files: List[FileEntry] = []
    leaves: List[str] = []
    
    for path, kind in inputs:
        # Calculer le hash du fichier
        sha256 = calc_file_sha256(path)
        leaves.append(sha256)
        
        # Créer l'entrée de fichier
        file_entry = FileEntry(
            path=str(path),
            kind=kind,
            size=path.stat().st_size,
            sha256=sha256
        )
        files.append(file_entry)
    
    # Calculer le root Merkle
    merkle_root = build_merkle(leaves)
    
    # Créer le manifest
    manifest = Manifest(
        run_path=run_path,
        files=files,
        merkle_root=merkle_root,
        notes=f"Audit Pack generated at {datetime.now(timezone.utc).isoformat()}"
    )
    
    return manifest


def write_zip(manifest: Manifest, out_dir: str = "dist/") -> Path:
    """
    Écrit le pack ZIP avec le manifest.
    
    Args:
        manifest: Manifest à inclure
        out_dir: Répertoire de sortie
    
    Returns:
        Chemin vers le pack ZIP créé
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack_name = f"pack-{timestamp}.zip"
    pack_path = out_path / pack_name
    
    with zipfile.ZipFile(pack_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Ajouter le manifest à la racine
        zf.writestr("manifest.json", manifest.model_dump_json())
        
        # Ajouter tous les fichiers du manifest
        for file_entry in manifest.files:
            file_path = Path(file_entry.path)
            if file_path.exists():
                zf.write(file_path, file_path.name)
    
    return pack_path


def verify_pack(pack_path: Path) -> Tuple[bool, str]:
    """
    Vérifie l'intégrité d'un pack.
    
    Args:
        pack_path: Chemin vers le pack ZIP
    
    Returns:
        Tuple (succès, raison)
    """
    try:
        with zipfile.ZipFile(pack_path, 'r') as zf:
            # Lire le manifest
            manifest_data = zf.read("manifest.json")
            manifest = Manifest.model_validate(orjson.loads(manifest_data))
            
            # Vérifier chaque fichier
            for file_entry in manifest.files:
                # Le fichier dans le ZIP a le nom du fichier seulement, pas le chemin complet
                file_name = Path(file_entry.path).name
                if file_name in zf.namelist():
                    # Calculer le hash du fichier dans le ZIP
                    file_data = zf.read(file_name)
                    actual_hash = hashlib.sha256(file_data).hexdigest()
                    
                    if actual_hash != file_entry.sha256:
                        return False, f"hash_mismatch for {file_entry.path}"
                else:
                    return False, f"missing_file {file_entry.path}"
            
            return True, "ok"
            
    except Exception as e:
        return False, f"error: {str(e)}"

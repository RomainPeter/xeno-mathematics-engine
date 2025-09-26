"""
Helper pour le journaling append-only et Merkle-chaining simple.
"""

import hashlib
import json
import time
import os
from typing import Dict, Any
from .schemas import PCAP


def now_iso() -> str:
    """Retourne le timestamp ISO actuel."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def merkle_of(obj: Dict[str, Any]) -> str:
    """Calcule le hash Merkle d'un objet."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def write_pcap(entry: PCAP, out_dir: str = "out/pcap") -> str:
    """
    Écrit un PCAP dans le répertoire de sortie.
    Retourne le chemin du fichier créé.
    """
    os.makedirs(out_dir, exist_ok=True)
    digest = merkle_of(entry.model_dump())
    timestamp = int(time.time() * 1000)
    filename = f"{timestamp}_{digest[:8]}.json"
    path = os.path.join(out_dir, filename)
    
    with open(path, "w") as f:
        f.write(entry.model_dump_json(indent=2))
    
    return path


def read_pcap(filepath: str) -> PCAP:
    """Lit un PCAP depuis un fichier."""
    with open(filepath, "r") as f:
        return PCAP.model_validate_json(f.read())


def list_pcaps(pcap_dir: str = "out/pcap") -> List[str]:
    """Liste tous les fichiers PCAP dans un répertoire."""
    if not os.path.exists(pcap_dir):
        return []
    
    pcap_files = []
    for filename in sorted(os.listdir(pcap_dir)):
        if filename.endswith('.json'):
            pcap_files.append(os.path.join(pcap_dir, filename))
    
    return pcap_files


def verify_pcap_chain(pcap_dir: str = "out/pcap") -> Dict[str, Any]:
    """
    Vérifie l'intégrité de la chaîne de PCAPs.
    Retourne un rapport de vérification.
    """
    pcap_files = list_pcaps(pcap_dir)
    
    if not pcap_files:
        return {"status": "empty", "count": 0}
    
    verification_results = {
        "status": "ok",
        "count": len(pcap_files),
        "files": [],
        "errors": []
    }
    
    for filepath in pcap_files:
        try:
            pcap = read_pcap(filepath)
            
            # Vérifier l'intégrité du PCAP
            computed_hash = merkle_of(pcap.model_dump())
            file_digest = os.path.basename(filepath).split('_')[1].split('.')[0]
            
            is_valid = computed_hash.startswith(file_digest)
            
            verification_results["files"].append({
                "file": os.path.basename(filepath),
                "operator": pcap.operator,
                "case_id": pcap.case_id,
                "verdict": pcap.verdict,
                "valid": is_valid,
                "timestamp": pcap.ts
            })
            
            if not is_valid:
                verification_results["errors"].append(f"Hash mismatch in {filepath}")
                verification_results["status"] = "error"
                
        except Exception as e:
            verification_results["errors"].append(f"Error reading {filepath}: {str(e)}")
            verification_results["status"] = "error"
    
    return verification_results

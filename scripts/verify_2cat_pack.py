#!/usr/bin/env python3
"""
Script de vérification du pack 2cat avec logique de skip.
Équivalent Python du script bash pour compatibilité Windows.
"""
import os
import sys
import hashlib
import subprocess
from pathlib import Path


def main():
    """Vérifie le pack 2cat avec logique de skip."""
    # Configuration
    pack_path = Path("vendor/2cat/2cat-pack.tar.gz")
    sig_path = Path("vendor/2cat/2cat-pack.tar.gz.minisig")
    lock_path = Path("vendor/2cat/2cat.lock")
    
    # Vérifier l'existence des fichiers
    missing_files = []
    if not pack_path.exists():
        missing_files.append(str(pack_path))
    if not sig_path.exists():
        missing_files.append(str(sig_path))
    if not lock_path.exists():
        missing_files.append(str(lock_path))
    
    # Skip si fichiers manquants et pas forcé
    if missing_files:
        force_verify = os.environ.get("FORCE_VERIFY_2CAT", "0")
        if force_verify != "1":
            print(f"2cat verification skipped (missing files: {', '.join(missing_files)}). Set FORCE_VERIFY_2CAT=1 to enforce.")
            sys.exit(0)
        else:
            print(f"Missing files: {', '.join(missing_files)} and FORCE_VERIFY_2CAT=1 set. Failing.")
            sys.exit(2)
    
    try:
        # Lire le fichier lock
        lock_content = lock_path.read_text()
        expected_sha = None
        expected_size = None
        pubkey = None
        
        for line in lock_content.split('\n'):
            if line.startswith('sha256:'):
                expected_sha = line.split(':', 1)[1].strip()
            elif line.startswith('size:'):
                expected_size = int(line.split(':', 1)[1].strip())
            elif line.startswith('pubkey:'):
                pubkey = line.split(':', 1)[1].strip()
        
        if not all([expected_sha, expected_size is not None, pubkey]):
            print("Invalid lock file format")
            sys.exit(6)
        
        # Vérifier SHA256
        with open(pack_path, 'rb') as f:
            content = f.read()
            actual_sha = hashlib.sha256(content).hexdigest()
        
        if expected_sha != actual_sha:
            print(f"SHA256 mismatch: expected {expected_sha}, got {actual_sha}")
            sys.exit(3)
        
        # Vérifier la taille
        actual_size = len(content)
        if expected_size != actual_size:
            print(f"Size mismatch: expected {expected_size}, got {actual_size}")
            sys.exit(4)
        
        # Vérifier la signature (si minisign est disponible)
        try:
            result = subprocess.run([
                'minisign', '-V', '-P', pubkey, '-m', str(pack_path), '-x', str(sig_path)
            ], capture_output=True, text=True, check=True)
            print(f"2cat pack verified (sha256: {actual_sha}, size: {actual_size})")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Signature verification failed or minisign not available")
            sys.exit(5)
            
    except Exception as e:
        print(f"Error during verification: {e}")
        sys.exit(7)


if __name__ == "__main__":
    main()
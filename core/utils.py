"""
Utilitaires pour le Proof Engine for Code v0.
"""

import os
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Optional


def summarize_repo(base_dir: str = "demo_repo") -> str:
    """
    Résume le contenu d'un repository.
    Retourne une description textuelle du repo.
    """
    if not os.path.exists(base_dir):
        return "Repository not found"
    
    summary_parts = []
    
    # Analyser la structure
    if os.path.exists(os.path.join(base_dir, "src")):
        summary_parts.append("src/ directory with source code")
    
    if os.path.exists(os.path.join(base_dir, "tests")):
        summary_parts.append("tests/ directory with test files")
    
    # Compter les fichiers Python
    py_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.relpath(os.path.join(root, file), base_dir))
    
    if py_files:
        summary_parts.append(f"{len(py_files)} Python files")
    
    # Analyser le contenu des fichiers principaux
    main_files = []
    for file in py_files:
        if not file.startswith('__') and not file.startswith('test_'):
            main_files.append(file)
    
    if main_files:
        summary_parts.append(f"main files: {', '.join(main_files[:3])}")
    
    return "small toy repo with " + ", ".join(summary_parts)


def run_command(cmd: List[str], cwd: str, timeout: int = 30) -> tuple[int, str, str]:
    """
    Exécute une commande dans un répertoire.
    
    Args:
        cmd: Commande à exécuter
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        
    Returns:
        Tuple[returncode, stdout, stderr]
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def create_temp_workspace(base_dir: str) -> str:
    """
    Crée un workspace temporaire basé sur un répertoire.
    
    Args:
        base_dir: Répertoire de base à copier
        
    Returns:
        Chemin du workspace temporaire
    """
    import uuid
    import tempfile
    
    temp_dir = os.path.join(tempfile.gettempdir(), f"proofengine_{uuid.uuid4().hex[:8]}")
    shutil.copytree(base_dir, temp_dir)
    return temp_dir


def cleanup_workspace(workspace_dir: str) -> None:
    """
    Nettoie un workspace temporaire.
    
    Args:
        workspace_dir: Répertoire à supprimer
    """
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir, ignore_errors=True)


def get_file_hash(filepath: str) -> str:
    """
    Calcule le hash SHA256 d'un fichier.
    
    Args:
        filepath: Chemin du fichier
        
    Returns:
        Hash SHA256 du fichier
    """
    import hashlib
    
    if not os.path.exists(filepath):
        return ""
    
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def compare_directories(dir1: str, dir2: str) -> Dict[str, Any]:
    """
    Compare deux répertoires et retourne les différences.
    
    Args:
        dir1: Premier répertoire
        dir2: Deuxième répertoire
        
    Returns:
        Dictionnaire avec les différences
    """
    def get_files(dir_path: str) -> Dict[str, str]:
        files = {}
        if os.path.exists(dir_path):
            for root, dirs, filenames in os.walk(dir_path):
                for filename in filenames:
                    if filename.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, filename), dir_path)
                        files[rel_path] = get_file_hash(os.path.join(root, filename))
        return files
    
    files1 = get_files(dir1)
    files2 = get_files(dir2)
    
    all_files = set(files1.keys()) | set(files2.keys())
    
    differences = {
        "added": [],
        "removed": [],
        "modified": [],
        "unchanged": []
    }
    
    for file in all_files:
        if file in files1 and file in files2:
            if files1[file] == files2[file]:
                differences["unchanged"].append(file)
            else:
                differences["modified"].append(file)
        elif file in files1:
            differences["removed"].append(file)
        else:
            differences["added"].append(file)
    
    return differences


def validate_python_syntax(filepath: str) -> tuple[bool, str]:
    """
    Valide la syntaxe Python d'un fichier.
    
    Args:
        filepath: Chemin du fichier Python
        
    Returns:
        Tuple[is_valid, error_message]
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            compile(f.read(), filepath, 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def get_python_files(directory: str) -> List[str]:
    """
    Retourne la liste des fichiers Python dans un répertoire.
    
    Args:
        directory: Répertoire à analyser
        
    Returns:
        Liste des chemins de fichiers Python
    """
    py_files = []
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
    return py_files

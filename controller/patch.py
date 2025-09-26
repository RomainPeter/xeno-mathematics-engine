"""
Gestion des patches et workspace pour le Proof Engine for Code v0.
Applique des patches unifiés sur un workspace.
"""

import subprocess
import tempfile
import shutil
import os
import uuid
from typing import Optional, Dict, Any


class Workspace:
    """Gestionnaire de workspace pour l'application de patches."""
    
    def __init__(self, base_dir: str = "demo_repo"):
        """
        Initialise un workspace basé sur un répertoire de base.
        
        Args:
            base_dir: Répertoire de base à copier
        """
        self.base_dir = base_dir
        self.work_dir = os.path.join(".work", str(uuid.uuid4())[:8])
        
        if not os.path.exists(base_dir):
            raise ValueError(f"Base directory {base_dir} does not exist")
        
        # Copier le répertoire de base
        shutil.copytree(base_dir, self.work_dir)
    
    def apply_unified_diff(self, patch_text: str) -> bool:
        """
        Applique un patch unifié sur le workspace.
        
        Args:
            patch_text: Contenu du patch unifié
            
        Returns:
            bool: True si le patch a été appliqué avec succès
        """
        if not patch_text.strip():
            return False
        
        try:
            # Utiliser git apply si disponible
            result = subprocess.run(
                ["git", "apply", "-p0", "-"],
                input=patch_text.encode(),
                cwd=self.work_dir,
                capture_output=True,
                check=True
            )
            return True
            
        except subprocess.CalledProcessError:
            # Fallback: utiliser patch si git apply échoue
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                    f.write(patch_text)
                    patch_file = f.name
                
                result = subprocess.run(
                    ["patch", "-p0", "-i", patch_file],
                    cwd=self.work_dir,
                    capture_output=True,
                    check=True
                )
                
                os.unlink(patch_file)
                return True
                
            except subprocess.CalledProcessError:
                return False
            except Exception:
                return False
        except Exception:
            return False
    
    def get_changed_files(self) -> list[str]:
        """
        Retourne la liste des fichiers modifiés.
        
        Returns:
            List[str]: Liste des chemins de fichiers modifiés
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            # Fallback: comparer avec le répertoire de base
            return self._compare_with_base()
        except Exception:
            return []
    
    def _compare_with_base(self) -> list[str]:
        """Compare avec le répertoire de base pour trouver les changements."""
        changed_files = []
        
        for root, dirs, files in os.walk(self.work_dir):
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.work_dir)
                    base_path = os.path.join(self.base_dir, rel_path)
                    work_path = os.path.join(self.work_dir, rel_path)
                    
                    if os.path.exists(base_path):
                        # Comparer les fichiers
                        try:
                            with open(base_path, 'rb') as f1, open(work_path, 'rb') as f2:
                                if f1.read() != f2.read():
                                    changed_files.append(rel_path)
                        except Exception:
                            pass
                    else:
                        # Nouveau fichier
                        changed_files.append(rel_path)
        
        return changed_files
    
    def get_diff(self) -> str:
        """
        Retourne le diff du workspace.
        
        Returns:
            str: Diff du workspace
        """
        try:
            result = subprocess.run(
                ["git", "diff"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
        except Exception:
            return ""
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du workspace.
        
        Returns:
            Dict[str, Any]: Statut du workspace
        """
        return {
            "work_dir": self.work_dir,
            "base_dir": self.base_dir,
            "changed_files": self.get_changed_files(),
            "diff": self.get_diff(),
            "exists": os.path.exists(self.work_dir)
        }
    
    def cleanup(self) -> None:
        """Nettoie le workspace temporaire."""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir, ignore_errors=True)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class PatchManager:
    """Gestionnaire de patches avec validation."""
    
    def __init__(self, base_dir: str = "demo_repo"):
        """Initialise le gestionnaire de patches."""
        self.base_dir = base_dir
    
    def validate_patch(self, patch_text: str) -> Dict[str, Any]:
        """
        Valide un patch avant application.
        
        Args:
            patch_text: Contenu du patch
            
        Returns:
            Dict[str, Any]: Résultats de la validation
        """
        validation = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        if not patch_text.strip():
            validation["errors"].append("Empty patch")
            return validation
        
        # Vérifier le format du patch
        lines = patch_text.split('\n')
        if not any(line.startswith('---') or line.startswith('+++') for line in lines):
            validation["errors"].append("Invalid patch format")
            return validation
        
        # Vérifier la syntaxe Python si applicable
        python_files = []
        for line in lines:
            if line.startswith('+++') and line.endswith('.py'):
                python_files.append(line.split()[-1])
        
        if python_files:
            validation["warnings"].append(f"Python files affected: {python_files}")
        
        validation["valid"] = True
        return validation
    
    def apply_patch(self, patch_text: str) -> Dict[str, Any]:
        """
        Applique un patch et retourne les résultats.
        
        Args:
            patch_text: Contenu du patch
            
        Returns:
            Dict[str, Any]: Résultats de l'application
        """
        # Valider le patch
        validation = self.validate_patch(patch_text)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Patch validation failed",
                "validation": validation
            }
        
        # Appliquer le patch
        with Workspace(self.base_dir) as ws:
            success = ws.apply_unified_diff(patch_text)
            
            if success:
                return {
                    "success": True,
                    "workspace": ws.get_status(),
                    "validation": validation
                }
            else:
                return {
                    "success": False,
                    "error": "Patch application failed",
                    "validation": validation
                }
    
    def get_patch_info(self, patch_text: str) -> Dict[str, Any]:
        """
        Analyse un patch et retourne des informations.
        
        Args:
            patch_text: Contenu du patch
            
        Returns:
            Dict[str, Any]: Informations sur le patch
        """
        lines = patch_text.split('\n')
        
        # Compter les lignes ajoutées/supprimées
        added_lines = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        # Identifier les fichiers affectés
        files_affected = set()
        for line in lines:
            if line.startswith('---') or line.startswith('+++'):
                file_path = line.split()[-1] if ' ' in line else line[3:]
                if file_path and file_path != '/dev/null':
                    files_affected.add(file_path)
        
        return {
            "total_lines": len(lines),
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "files_affected": list(files_affected),
            "size": len(patch_text),
            "complexity": (added_lines + removed_lines) / max(1, len(files_affected))
        }

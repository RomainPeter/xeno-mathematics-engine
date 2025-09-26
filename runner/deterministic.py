"""
Exécuteur déterministe pour le Proof Engine for Code v0.
Gère l'exécution hermétique avec seeds fixes et collecte de métriques.
"""

import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from ..core.schemas import PCAP, Proof, VJustification
from ..obligations.policies import PolicyEngine


class DeterministicRunner:
    """Exécuteur déterministe avec environnement verrouillé."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialise l'exécuteur avec une configuration."""
        self.config = config or {}
        self.policy_engine = PolicyEngine(config)
        self.execution_history: List[Dict[str, Any]] = []
    
    def run_and_prove(self, context: Dict[str, Any], obligations: List[Dict[str, Any]], 
                     seed: int = None) -> Tuple[List[Proof], VJustification]:
        """
        Exécute les vérifications de manière déterministe.
        Retourne les preuves et le coût total.
        """
        start_time = self._get_time_ms()
        
        # Fixer la graine pour la reproductibilité
        if seed is not None:
            import random
            random.seed(seed)
        
        # Créer un environnement hermétique
        with self._create_hermetic_env() as env:
            # Exécuter les politiques
            proofs, cost = self.policy_engine.check_obligations({
                **context,
                "obligations": obligations
            })
            
            # Enregistrer l'exécution
            self._record_execution(context, proofs, cost, seed)
            
            return proofs, cost
    
    def _create_hermetic_env(self):
        """Crée un environnement hermétique pour l'exécution."""
        class HermeticEnv:
            def __init__(self, runner):
                self.runner = runner
                self.original_env = os.environ.copy()
                self.temp_dir = None
            
            def __enter__(self):
                # Créer un répertoire temporaire isolé
                self.temp_dir = tempfile.mkdtemp(prefix="proof_engine_")
                
                # Variables d'environnement isolées
                os.environ.update({
                    "PYTHONPATH": self.temp_dir,
                    "TMPDIR": self.temp_dir,
                    "TEMP": self.temp_dir,
                    "TMP": self.temp_dir
                })
                
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restaurer l'environnement original
                os.environ.clear()
                os.environ.update(self.original_env)
                
                # Nettoyer le répertoire temporaire
                if self.temp_dir and os.path.exists(self.temp_dir):
                    import shutil
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        return HermeticEnv(self)
    
    def _record_execution(self, context: Dict[str, Any], proofs: List[Proof], 
                         cost: VJustification, seed: int = None) -> None:
        """Enregistre une exécution dans l'historique."""
        record = {
            "timestamp": self._get_timestamp(),
            "seed": seed,
            "context_keys": list(context.keys()),
            "proofs_count": len(proofs),
            "cost": cost.to_dict(),
            "all_passed": all(p.passed for p in proofs)
        }
        
        self.execution_history.append(record)
    
    def _get_time_ms(self) -> int:
        """Retourne le temps actuel en millisecondes."""
        return int(time.time() * 1000)
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'exécution."""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for r in self.execution_history if r.get("all_passed", False))
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        avg_cost = sum(r.get("cost", {}).get("audit_cost", 0) for r in self.execution_history) / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": success_rate,
            "average_cost": avg_cost,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }
    
    def reset_history(self) -> None:
        """Remet à zéro l'historique d'exécution."""
        self.execution_history = []


class HermeticExecutor:
    """Exécuteur hermétique pour les tests et vérifications."""
    
    def __init__(self, timeout: int = 30):
        """Initialise l'exécuteur avec un timeout."""
        self.timeout = timeout
        self.results: List[Dict[str, Any]] = []
    
    def execute_test(self, test_code: str, seed: int = None) -> Dict[str, Any]:
        """Exécute un test de manière hermétique."""
        start_time = self._get_time_ms()
        
        try:
            # Créer un fichier temporaire pour le test
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_code)
                test_file = f.name
            
            # Exécuter le test
            result = subprocess.run(
                ["python", test_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Nettoyer
            os.unlink(test_file)
            
            execution_time = self._get_time_ms() - start_time
            
            result_record = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": execution_time,
                "seed": seed,
                "timestamp": self._get_timestamp()
            }
            
            self.results.append(result_record)
            return result_record
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Timeout après {self.timeout}s",
                "execution_time_ms": self._get_time_ms() - start_time,
                "seed": seed,
                "timestamp": self._get_timestamp()
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Erreur d'exécution: {str(e)}",
                "execution_time_ms": self._get_time_ms() - start_time,
                "seed": seed,
                "timestamp": self._get_timestamp()
            }
    
    def execute_linter(self, code: str, linter: str = "ruff") -> Dict[str, Any]:
        """Exécute un linter de manière hermétique."""
        start_time = self._get_time_ms()
        
        try:
            # Créer un fichier temporaire pour le code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            # Exécuter le linter
            if linter == "ruff":
                result = subprocess.run(
                    ["ruff", "check", code_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif linter == "mypy":
                result = subprocess.run(
                    ["mypy", code_file, "--ignore-missing-imports"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
            else:
                raise ValueError(f"Linter non supporté: {linter}")
            
            # Nettoyer
            os.unlink(code_file)
            
            execution_time = self._get_time_ms() - start_time
            
            result_record = {
                "linter": linter,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": execution_time,
                "timestamp": self._get_timestamp()
            }
            
            self.results.append(result_record)
            return result_record
            
        except Exception as e:
            return {
                "linter": linter,
                "success": False,
                "stdout": "",
                "stderr": f"Erreur {linter}: {str(e)}",
                "execution_time_ms": self._get_time_ms() - start_time,
                "timestamp": self._get_timestamp()
            }
    
    def _get_time_ms(self) -> int:
        """Retourne le temps actuel en millisecondes."""
        return int(time.time() * 1000)
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des résultats."""
        if not self.results:
            return {"total_executions": 0}
        
        total_executions = len(self.results)
        successful_executions = sum(1 for r in self.results if r.get("success", False))
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        avg_execution_time = sum(r.get("execution_time_ms", 0) for r in self.results) / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": success_rate,
            "average_execution_time_ms": avg_execution_time,
            "last_result": self.results[-1] if self.results else None
        }

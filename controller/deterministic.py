"""
Contrôleur déterministe pour le Proof Engine for Code v0.
Orchestre les vérifications et évaluations.
"""

from typing import Dict, Any, List, Tuple
from .obligations import evaluate_obligations, get_obligation_details, get_violation_summary
from .patch import Workspace, PatchManager
from proofengine.core.schemas import ObligationResults, VJustification
from proofengine.core.delta import compute_delta
import time


class DeterministicController:
    """Contrôleur déterministe pour les vérifications."""
    
    def __init__(self, base_dir: str = "demo_repo"):
        """Initialise le contrôleur."""
        self.base_dir = base_dir
        self.patch_manager = PatchManager(base_dir)
        self.evaluation_history: List[Dict[str, Any]] = []
    
    def evaluate_patch(self, patch_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Évalue un patch de manière déterministe.
        
        Args:
            patch_text: Contenu du patch unifié
            context: Contexte additionnel
            
        Returns:
            Dict[str, Any]: Résultats de l'évaluation
        """
        start_time = time.time()
        
        # Valider le patch
        validation = self.patch_manager.validate_patch(patch_text)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Patch validation failed",
                "validation": validation,
                "evaluation_time_ms": int((time.time() - start_time) * 1000)
            }
        
        # Appliquer le patch
        with Workspace(self.base_dir) as ws:
            apply_success = ws.apply_unified_diff(patch_text)
            
            if not apply_success:
                return {
                    "success": False,
                    "error": "Patch application failed",
                    "evaluation_time_ms": int((time.time() - start_time) * 1000)
                }
            
            # Évaluer les obligations
            obligation_results = evaluate_obligations(ws.work_dir)
            
            # Calculer les métriques
            violations = obligation_results.violations_count()
            delta_metrics = self._calculate_delta_metrics(ws, context or {})
            
            # Créer la justification
            justification = VJustification(
                time_ms=int((time.time() - start_time) * 1000),
                backtracks=0,
                audit_cost_ms=int(violations * 100),
                tech_debt=violations,
                llm_time_ms=None,
                model=None
            )
            
            # Résultats de l'évaluation
            evaluation_result = {
                "success": obligation_results.all_passed(),
                "obligation_results": obligation_results,
                "violations": violations,
                "delta_metrics": delta_metrics,
                "justification": justification,
                "workspace_status": ws.get_status(),
                "evaluation_time_ms": int((time.time() - start_time) * 1000)
            }
            
            # Enregistrer dans l'historique
            self._record_evaluation(patch_text, evaluation_result)
            
            return evaluation_result
    
    def _calculate_delta_metrics(self, workspace: Workspace, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calcule les métriques δ pour un workspace."""
        try:
            # Obtenir les fichiers modifiés
            changed_files = workspace.get_changed_files()
            
            if not changed_files:
                return {"delta_total": 0.0, "components": {}}
            
            # Calculer le delta
            delta_metrics = compute_delta(
                H_before=context.get("H_before", []),
                H_after=context.get("H_after", []),
                E_before=context.get("E_before", []),
                E_after=context.get("E_after", []),
                K_before=context.get("K_before", []),
                K_after=context.get("K_after", []),
                changed_paths=changed_files,
                before_dir=self.base_dir,
                after_dir=workspace.work_dir,
                violations=context.get("violations", 0)
            )
            
            return delta_metrics.to_dict()
            
        except Exception as e:
            return {
                "delta_total": 1.0,
                "components": {"error": str(e)},
                "error": str(e)
            }
    
    def batch_evaluate(self, patches: List[str], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Évalue plusieurs patches en lot.
        
        Args:
            patches: Liste des patches à évaluer
            context: Contexte partagé
            
        Returns:
            List[Dict[str, Any]]: Résultats de chaque évaluation
        """
        results = []
        
        for i, patch in enumerate(patches):
            try:
                result = self.evaluate_patch(patch, context)
                result["patch_index"] = i
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": f"Evaluation failed: {str(e)}",
                    "patch_index": i,
                    "evaluation_time_ms": 0
                })
        
        return results
    
    def get_best_patch(self, patches: List[str], context: Dict[str, Any] = None) -> Tuple[int, Dict[str, Any]]:
        """
        Trouve le meilleur patch parmi une liste.
        
        Args:
            patches: Liste des patches à comparer
            context: Contexte d'évaluation
            
        Returns:
            Tuple[index, result]: Index et résultat du meilleur patch
        """
        results = self.batch_evaluate(patches, context)
        
        if not results:
            return -1, {"error": "No patches to evaluate"}
        
        # Trouver le meilleur résultat
        best_index = -1
        best_score = -1.0
        
        for i, result in enumerate(results):
            if result.get("success", False):
                # Score basé sur les violations et le delta
                violations = result.get("violations", 0)
                delta_total = result.get("delta_metrics", {}).get("delta_total", 1.0)
                
                # Score inversé (moins de violations et delta = meilleur)
                score = 1.0 - (violations * 0.1 + delta_total * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_index = i
        
        if best_index >= 0:
            return best_index, results[best_index]
        else:
            # Aucun patch n'a réussi, retourner le premier
            return 0, results[0]
    
    def _record_evaluation(self, patch_text: str, result: Dict[str, Any]) -> None:
        """Enregistre une évaluation dans l'historique."""
        record = {
            "patch_length": len(patch_text),
            "success": result.get("success", False),
            "violations": result.get("violations", 0),
            "delta_total": result.get("delta_metrics", {}).get("delta_total", 0.0),
            "evaluation_time_ms": result.get("evaluation_time_ms", 0),
            "timestamp": self._get_timestamp()
        }
        
        self.evaluation_history.append(record)
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'évaluation."""
        if not self.evaluation_history:
            return {"total_evaluations": 0}
        
        total_evaluations = len(self.evaluation_history)
        successful_evaluations = sum(1 for e in self.evaluation_history if e["success"])
        success_rate = successful_evaluations / total_evaluations if total_evaluations > 0 else 0
        
        avg_violations = sum(e["violations"] for e in self.evaluation_history) / total_evaluations
        avg_delta = sum(e["delta_total"] for e in self.evaluation_history) / total_evaluations
        avg_time = sum(e["evaluation_time_ms"] for e in self.evaluation_history) / total_evaluations
        
        return {
            "total_evaluations": total_evaluations,
            "successful_evaluations": successful_evaluations,
            "success_rate": success_rate,
            "average_violations": avg_violations,
            "average_delta": avg_delta,
            "average_time_ms": avg_time,
            "last_evaluation": self.evaluation_history[-1] if self.evaluation_history else None
        }
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    def clear_history(self) -> None:
        """Remet à zéro l'historique."""
        self.evaluation_history = []

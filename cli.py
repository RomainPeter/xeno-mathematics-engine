"""
Orchestrateur principal pour le Proof Engine for Code v0.
Gère la boucle complète avec rollback et re-plan.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from proofengine.core.schemas import XState, PCAP, VJustification
from proofengine.core.pcap import now_iso, write_pcap, merkle_of
from proofengine.core.utils import summarize_repo
from controller.patch import Workspace
from controller.deterministic import DeterministicController
from controller.obligations import evaluate_obligations
from proofengine.core.delta import compute_delta
from planner.meta import MetacognitivePlanner
from generator.stochastic import StochasticGenerator
from verifier.runner import verify_pcap_dir
from metrics.collect import MetricsCollector
from metrics.report import ReportGenerator


class ProofEngineOrchestrator:
    """Orchestrateur principal du Proof Engine."""
    
    def __init__(self, base_dir: str = "demo_repo", output_dir: str = "out"):
        """Initialise l'orchestrateur."""
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.pcap_dir = os.path.join(output_dir, "pcap")
        self.metrics_dir = os.path.join(output_dir, "metrics")
        self.audit_dir = os.path.join(output_dir, "audit")
        
        # Créer les répertoires de sortie
        os.makedirs(self.pcap_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.audit_dir, exist_ok=True)
        
        # Initialiser les composants
        self.planner = MetacognitivePlanner()
        self.generator = StochasticGenerator()
        self.controller = DeterministicController(base_dir)
        self.metrics_collector = MetricsCollector()
        self.report_generator = ReportGenerator()
        
        # État de l'orchestrateur
        self.current_state: Optional[XState] = None
        self.execution_history: List[Dict[str, Any]] = []
    
    def run_demo(self, case_id: str = "demo_case", goal: str = None) -> Dict[str, Any]:
        """
        Exécute une démonstration complète.
        
        Args:
            case_id: Identifiant du cas
            goal: Objectif à atteindre
            
        Returns:
            Dict[str, Any]: Résultats de la démonstration
        """
        if goal is None:
            goal = f"Improve {case_id} under constraints"
        
        print(f"🎯 Démarrage de la démonstration: {case_id}")
        print(f"📋 Objectif: {goal}")
        
        # Initialiser l'état
        self.current_state = self._create_initial_state(case_id, goal)
        
        # Phase 1: Planification
        print("🧠 Phase 1: Planification métacognitive...")
        plan_result = self._execute_planning_phase(goal)
        
        # Phase 2: Génération et évaluation
        print("⚡ Phase 2: Génération stochastique et évaluation...")
        generation_result = self._execute_generation_phase(goal)
        
        # Phase 3: Vérification et attestation
        print("🔍 Phase 3: Vérification et attestation...")
        verification_result = self._execute_verification_phase()
        
        # Phase 4: Métriques et rapports
        print("📊 Phase 4: Génération des métriques...")
        metrics_result = self._execute_metrics_phase()
        
        # Résultats finaux
        final_result = {
            "success": generation_result.get("success", False),
            "case_id": case_id,
            "goal": goal,
            "planning": plan_result,
            "generation": generation_result,
            "verification": verification_result,
            "metrics": metrics_result,
            "execution_time_ms": int((time.time() - self._start_time) * 1000)
        }
        
        print(f"✅ Démonstration terminée: {'SUCCÈS' if final_result['success'] else 'ÉCHEC'}")
        return final_result
    
    def _create_initial_state(self, case_id: str, goal: str) -> XState:
        """Crée l'état initial pour un cas."""
        return XState(
            H=[f"goal:{goal}"],
            E=[],
            K=["tests_ok", "lint_ok", "types_ok", "security_ok", "complexity_ok", "docstring_ok"],
            A=[],
            J=[],
            Sigma={"seed": 123, "case_id": case_id, "timestamp": now_iso()}
        )
    
    def _execute_planning_phase(self, goal: str) -> Dict[str, Any]:
        """Exécute la phase de planification."""
        try:
            # Résumer le repository
            repo_summary = summarize_repo(self.base_dir)
            
            # Proposer un plan
            plan = self.planner.propose_plan(
                goal=goal,
                x_summary=repo_summary,
                obligations=self.current_state.K,
                history=self.execution_history
            )
            
            # Créer le PCAP de planification
            pcap_plan = PCAP(
                ts=now_iso(),
                operator="plan",
                case_id=self.current_state.Sigma["case_id"],
                pre={"H": self.current_state.H, "K": self.current_state.K},
                post={"plan": plan.plan},
                obligations=self.current_state.K,
                justification=VJustification(
                    time_ms=plan.llm_meta.get("latency_ms", 0),
                    llm_time_ms=plan.llm_meta.get("latency_ms", 0),
                    model=plan.llm_meta.get("model", "unknown")
                ),
                proof_state_hash=merkle_of({"H": self.current_state.H, "K": self.current_state.K}),
                toolchain={"python": "3.11", "planner": "metacognitive"},
                llm_meta=plan.llm_meta,
                verdict="pass"
            )
            
            # Sauvegarder le PCAP
            write_pcap(pcap_plan, self.pcap_dir)
            
            return {
                "success": True,
                "plan": plan.plan,
                "estimated_success": plan.est_success,
                "estimated_cost": plan.est_cost,
                "notes": plan.notes,
                "pcap_file": f"plan_{int(time.time()*1000)}.json"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "plan": [],
                "estimated_success": 0.0,
                "estimated_cost": 0.0
            }
    
    def _execute_generation_phase(self, goal: str) -> Dict[str, Any]:
        """Exécute la phase de génération et évaluation."""
        try:
            # Générer des variantes
            variants = self.generator.propose_variants(
                task=goal,
                context=summarize_repo(self.base_dir),
                obligations=self.current_state.K,
                k=3
            )
            
            # Évaluer chaque variante
            best_patch = None
            best_result = None
            best_index = -1
            
            for i, variant in enumerate(variants):
                print(f"  🔧 Évaluation de la variante {i+1}/{len(variants)}...")
                
                # Évaluer le patch
                evaluation = self.controller.evaluate_patch(
                    patch_text=variant.patch_unified,
                    context={
                        "H_before": self.current_state.H,
                        "E_before": self.current_state.E,
                        "K_before": self.current_state.K
                    }
                )
                
                # Créer le PCAP d'évaluation
                pcap_eval = PCAP(
                    ts=now_iso(),
                    operator="verify",
                    case_id=self.current_state.Sigma["case_id"],
                    pre={"patch": variant.patch_unified[:100] + "..."},
                    post={"evaluation": evaluation},
                    obligations=self.current_state.K,
                    justification=evaluation.get("justification", VJustification()),
                    proof_state_hash=merkle_of(evaluation),
                    toolchain={"python": "3.11", "evaluator": "deterministic"},
                    llm_meta=variant.llm_meta,
                    verdict="pass" if evaluation.get("success", False) else "fail"
                )
                
                # Sauvegarder le PCAP
                write_pcap(pcap_eval, self.pcap_dir)
                
                # Vérifier si c'est le meilleur résultat
                if evaluation.get("success", False):
                    if best_patch is None or evaluation.get("violations", 0) < best_result.get("violations", 0):
                        best_patch = variant
                        best_result = evaluation
                        best_index = i
            
            # Résultats de la génération
            if best_patch:
                return {
                    "success": True,
                    "best_patch": best_patch.patch_unified,
                    "best_result": best_result,
                    "best_index": best_index,
                    "total_variants": len(variants),
                    "violations": best_result.get("violations", 0)
                }
            else:
                # Aucune variante n'a réussi, rollback
                return self._execute_rollback_phase(goal)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_variants": 0
            }
    
    def _execute_rollback_phase(self, goal: str) -> Dict[str, Any]:
        """Exécute la phase de rollback et replanification."""
        print("  🔄 Rollback et replanification...")
        
        try:
            # Créer le PCAP de rollback
            pcap_rollback = PCAP(
                ts=now_iso(),
                operator="rollback",
                case_id=self.current_state.Sigma["case_id"],
                pre={"reason": "all variants failed"},
                post={"action": "replan"},
                obligations=self.current_state.K,
                justification=VJustification(backtracks=1),
                proof_state_hash=merkle_of({"rollback": True}),
                toolchain={"python": "3.11", "action": "rollback"},
                verdict="fail"
            )
            
            # Sauvegarder le PCAP
            write_pcap(pcap_rollback, self.pcap_dir)
            
            # Replanifier
            replan = self.planner.replan_after_failure(
                goal=goal,
                previous_plan=["Generate variants", "Evaluate patches", "Apply best patch"],
                failure_reason="All variants failed evaluation",
                x_summary=summarize_repo(self.base_dir),
                obligations=self.current_state.K,
                evidence=["No successful variants found"]
            )
            
            # Créer le PCAP de replanification
            pcap_replan = PCAP(
                ts=now_iso(),
                operator="replan",
                case_id=self.current_state.Sigma["case_id"],
                pre={"failure": "all variants failed"},
                post={"new_plan": replan.plan},
                obligations=self.current_state.K,
                justification=VJustification(
                    time_ms=replan.llm_meta.get("latency_ms", 0),
                    llm_time_ms=replan.llm_meta.get("latency_ms", 0),
                    model=replan.llm_meta.get("model", "unknown")
                ),
                proof_state_hash=merkle_of({"replan": True}),
                toolchain={"python": "3.11", "action": "replan"},
                llm_meta=replan.llm_meta,
                verdict="pass"
            )
            
            # Sauvegarder le PCAP
            write_pcap(pcap_replan, self.pcap_dir)
            
            return {
                "success": False,
                "rollback": True,
                "replan": replan.plan,
                "estimated_success": replan.est_success,
                "notes": replan.notes
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rollback": True
            }
    
    def _execute_verification_phase(self) -> Dict[str, Any]:
        """Exécute la phase de vérification."""
        try:
            # Vérifier tous les PCAPs
            verification_result = verify_pcap_dir(self.pcap_dir, self.audit_dir)
            
            return {
                "success": True,
                "verification": verification_result,
                "attestation_file": verification_result.get("attestation_file")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_metrics_phase(self) -> Dict[str, Any]:
        """Exécute la phase de métriques."""
        try:
            # Collecter les métriques
            metrics = self.metrics_collector.collect_metrics(self.pcap_dir)
            
            # Générer les rapports
            markdown_report = self.report_generator.save_report(
                metrics, self.metrics_dir, "markdown"
            )
            json_report = self.report_generator.save_report(
                metrics, self.metrics_dir, "json"
            )
            
            return {
                "success": True,
                "metrics": metrics,
                "markdown_report": markdown_report,
                "json_report": json_report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _start_time(self) -> float:
        """Retourne le temps de début."""
        return time.time()


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Proof Engine for Code v0")
    parser.add_argument("--case", default="sanitize_input", help="Cas de test")
    parser.add_argument("--goal", help="Objectif personnalisé")
    parser.add_argument("--base-dir", default="demo_repo", help="Répertoire de base")
    parser.add_argument("--output-dir", default="out", help="Répertoire de sortie")
    
    args = parser.parse_args()
    
    # Créer l'orchestrateur
    orchestrator = ProofEngineOrchestrator(args.base_dir, args.output_dir)
    
    # Exécuter la démonstration
    result = orchestrator.run_demo(args.case, args.goal)
    
    # Afficher les résultats
    print("\n📋 Résultats:")
    print(f"  Succès: {result['success']}")
    print(f"  Temps d'exécution: {result['execution_time_ms']}ms")
    
    if result['generation'].get('success'):
        print(f"  Violations: {result['generation'].get('violations', 0)}")
        print(f"  Variantes testées: {result['generation'].get('total_variants', 0)}")
    
    if result['metrics'].get('success'):
        print(f"  Rapport Markdown: {result['metrics'].get('markdown_report')}")
        print(f"  Rapport JSON: {result['metrics'].get('json_report')}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())

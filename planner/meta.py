"""
Planificateur métacognitif pour le Proof Engine for Code v0.
"""

from typing import List, Dict, Any, Optional
from proofengine.core.llm_client import LLMClient, LLMConfig
from proofengine.core.schemas import PlanProposal
from .prompts import PLANNER_SYSTEM, PLANNER_USER_TMPL, REPLAN_SYSTEM, REPLAN_USER_TMPL


class MetacognitivePlanner:
    """Planificateur métacognitif avec apprentissage."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.llm = LLMClient(config)
        self.planning_history: List[Dict[str, Any]] = []
    
    def propose_plan(self, goal: str, x_summary: str, obligations: List[str], 
                    history: List[Dict[str, Any]]) -> PlanProposal:
        """Propose un plan métacognitif."""
        history_summary = self._summarize_history(history[-5:])
        
        user_prompt = PLANNER_USER_TMPL.format(
            goal=goal,
            x_summary=x_summary,
            obligations=obligations,
            history=history_summary
        )
        
        try:
            data, meta = self.llm.generate_json(
                PLANNER_SYSTEM,
                user_prompt,
                seed=42,
                temperature=0.2,
                max_tokens=800
            )
            
            plan = data.get("plan", [])[:5]
            est_success = float(data.get("est_success", 0.5))
            est_cost = float(data.get("est_cost", 1.0))
            notes = data.get("notes", "")
            
            proposal = PlanProposal(
                plan=plan,
                est_success=est_success,
                est_cost=est_cost,
                notes=notes,
                llm_meta=meta
            )
            
            self._record_planning(goal, proposal, "initial")
            return proposal
            
        except Exception as e:
            return PlanProposal(
                plan=["Analyze current state", "Identify issues", "Apply fixes", "Verify results"],
                est_success=0.3,
                est_cost=5.0,
                notes=f"Fallback plan due to error: {str(e)}"
            )
    
    def replan_after_failure(self, goal: str, previous_plan: List[str], 
                            failure_reason: str, x_summary: str, 
                            obligations: List[str], evidence: List[str]) -> PlanProposal:
        """Replanifie après un échec."""
        user_prompt = REPLAN_USER_TMPL.format(
            goal=goal,
            previous_plan=previous_plan,
            failure_reason=failure_reason,
            x_summary=x_summary,
            obligations=obligations,
            evidence=evidence
        )
        
        try:
            data, meta = self.llm.generate_json(
                REPLAN_SYSTEM,
                user_prompt,
                seed=43,
                temperature=0.3,
                max_tokens=800
            )
            
            plan = data.get("plan", [])[:5]
            est_success = float(data.get("est_success", 0.4))
            est_cost = float(data.get("est_cost", 1.5))
            notes = data.get("notes", "")
            
            proposal = PlanProposal(
                plan=plan,
                est_success=est_success,
                est_cost=est_cost,
                notes=notes,
                llm_meta=meta
            )
            
            self._record_planning(goal, proposal, "replan", failure_reason)
            return proposal
            
        except Exception as e:
            return PlanProposal(
                plan=["Review failure", "Identify root cause", "Try alternative approach", "Verify carefully"],
                est_success=0.2,
                est_cost=7.0,
                notes=f"Fallback replan due to error: {str(e)}"
            )
    
    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        """Résume l'historique des PCAPs."""
        if not history:
            return "No previous attempts"
        
        summary_parts = []
        for entry in history:
            operator = entry.get("operator", "unknown")
            verdict = entry.get("verdict", "unknown")
            summary_parts.append(f"{operator}: {verdict}")
        
        return "; ".join(summary_parts)
    
    def _record_planning(self, goal: str, proposal: PlanProposal, 
                        plan_type: str, failure_reason: str = None) -> None:
        """Enregistre une session de planification."""
        record = {
            "goal": goal,
            "plan_type": plan_type,
            "plan": proposal.plan,
            "est_success": proposal.est_success,
            "est_cost": proposal.est_cost,
            "notes": proposal.notes,
            "failure_reason": failure_reason,
            "timestamp": self._get_timestamp()
        }
        
        self.planning_history.append(record)
    
    def get_planning_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de planification."""
        if not self.planning_history:
            return {"total_plans": 0}
        
        total_plans = len(self.planning_history)
        initial_plans = sum(1 for p in self.planning_history if p["plan_type"] == "initial")
        replan_attempts = sum(1 for p in self.planning_history if p["plan_type"] == "replan")
        
        avg_success = sum(p["est_success"] for p in self.planning_history) / total_plans
        avg_cost = sum(p["est_cost"] for p in self.planning_history) / total_plans
        
        return {
            "total_plans": total_plans,
            "initial_plans": initial_plans,
            "replan_attempts": replan_attempts,
            "average_estimated_success": avg_success,
            "average_estimated_cost": avg_cost,
            "last_plan": self.planning_history[-1] if self.planning_history else None
        }
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp formaté."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    def clear_history(self) -> None:
        """Remet à zéro l'historique."""
        self.planning_history = []
"""Metacognitive planner used in tests and orchestrator."""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from proofengine.core.schemas import PlanProposal, VJustification, XState


@dataclass
class PlannedAction:
    action_id: str
    description: str
    estimated_cost: VJustification
    confidence: float


@dataclass
class PlannedSequence:
    plan_id: str
    actions: List[PlannedAction]
    estimated_utility: float
    confidence: float


class MetacognitivePlanner:
    """Rule-based planner with deterministic seeds for reproducibility."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.seed = self.config.get("seed", 0)
        self.planning_history: List[Dict[str, Any]] = []

    def plan(self, state: XState, goal: str) -> PlannedSequence:
        actions = self._build_default_actions(goal)
        utility = sum(1.0 - action.estimated_cost.risk for action in actions)
        confidence = min(1.0, 0.6 + 0.05 * len(actions))
        plan = PlannedSequence(
            plan_id=f"plan-{hash(goal) & 0xffff:x}",
            actions=actions,
            estimated_utility=utility,
            confidence=confidence,
        )
        self._record_plan(goal, plan)
        return plan

    def propose_plan(
        self,
        goal: str,
        x_summary: str,
        obligations: List[str],
        history: List[Dict[str, Any]],
    ) -> PlanProposal:
        actions = [f"Analyse {item}" for item in obligations[:3]] or [
            "Inspect codebase",
            "Run tests",
        ]
        proposal = PlanProposal(
            plan=actions,
            est_success=0.7,
            est_cost=max(1.0, len(actions) * 0.5),
            notes=f"Generated locally for goal: {goal}",
            llm_meta={"latency_ms": 0, "model": "offline"},
        )
        self._record_plan(goal, proposal)
        return proposal

    def replan_after_failure(
        self,
        goal: str,
        previous_plan: List[str],
        failure_reason: str,
        x_summary: str,
        obligations: List[str],
        evidence: List[str],
    ) -> PlanProposal:
        refreshed = ["Review failure", "Adjust strategy"] + previous_plan[:2]
        proposal = PlanProposal(
            plan=refreshed,
            est_success=0.5,
            est_cost=max(1.0, len(refreshed) * 0.6),
            notes=f"Replan due to: {failure_reason}",
            llm_meta={"latency_ms": 0, "model": "offline"},
        )
        self._record_plan(goal, proposal, plan_type="replan")
        return proposal

    def execute_plan(
        self,
        state: XState,
        goal: str,
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        actions = self._build_default_actions(goal)
        history: List[Dict[str, Any]] = []
        new_state = XState(**state.to_dict())
        for idx, action in enumerate(actions):
            verdict = "pass" if action.confidence >= 0.5 else "fail"
            history.append(
                {
                    "action_id": action.action_id,
                    "verdict": verdict,
                    "cost": action.estimated_cost.to_dict(),
                    "timestamp": self._timestamp(),
                }
            )
            if verdict == "fail" and budget and budget.get("max_retries", 0) == 0:
                break
        success = all(entry["verdict"] == "pass" for entry in history)
        success_count = sum(1 for entry in history if entry["verdict"] == "pass")
        metrics = {
            "total_actions": len(history),
            "success_rate": success_count / len(history) if history else 0.0,
        }
        return {
            "success": success,
            "final_state": new_state,
            "execution_history": history,
            "metrics": metrics,
        }

    def get_planning_stats(self) -> Dict[str, Any]:
        if not self.planning_history:
            return {"total_plans": 0}
        total = len(self.planning_history)
        avg_success = sum(item["est_success"] for item in self.planning_history) / total
        return {
            "total_plans": total,
            "average_estimated_success": avg_success,
            "last_plan": self.planning_history[-1],
        }

    def clear_history(self) -> None:
        self.planning_history = []

    # Internal helpers -------------------------------------------------
    def _build_default_actions(self, goal: str) -> List[PlannedAction]:
        templates = [
            ("analyse", "Analyser le contexte"),
            ("mutate", "Générer des variantes"),
            ("verify", "Vérifier les obligations"),
        ]
        actions = []
        for idx, (slug, description) in enumerate(itertools.islice(itertools.cycle(templates), 3)):
            actions.append(
                PlannedAction(
                    action_id=f"{slug}-{idx}",
                    description=f"{description} pour {goal}",
                    estimated_cost=VJustification(
                        time_ms=200 + idx * 50,
                        audit_cost=0.5 + idx * 0.1,
                        risk=0.1 * idx,
                    ),
                    confidence=0.7 - idx * 0.1,
                )
            )
        return actions

    def _record_plan(self, goal: str, plan: Any, plan_type: str = "initial") -> None:
        self.planning_history.append(
            {
                "goal": goal,
                "plan_type": plan_type,
                "timestamp": self._timestamp(),
                "est_success": getattr(plan, "est_success", 0.6),
                "plan": getattr(
                    plan,
                    "plan",
                    [action.description for action in getattr(plan, "actions", [])],
                ),
            }
        )

    def _timestamp(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

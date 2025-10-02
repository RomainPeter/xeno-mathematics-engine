"""Deterministic controller orchestrating obligation checks in tests."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from proofengine.core.delta import compute_delta
from proofengine.core.schemas import VJustification

from .obligations import evaluate_obligations, get_obligation_details, get_violation_summary
from .patch import PatchManager, Workspace


class DeterministicController:
    """Evaluates unified diffs against a repository using deterministic policies."""

    def __init__(self, base_dir: str = "demo_repo"):
        self.base_dir = base_dir
        self.patch_manager = PatchManager(base_dir)
        self.evaluation_history: List[Dict[str, Any]] = []

    def evaluate_patch(
        self, patch_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        context = context or {}
        start = time.time()

        validation = self.patch_manager.validate_patch(patch_text)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Patch validation failed",
                "validation": validation,
                "evaluation_time_ms": int((time.time() - start) * 1000),
            }

        with Workspace(self.base_dir) as workspace:
            if not workspace.apply_unified_diff(patch_text):
                return {
                    "success": False,
                    "error": "Patch application failed",
                    "evaluation_time_ms": int((time.time() - start) * 1000),
                }

            obligation_results = evaluate_obligations(workspace.work_dir)
            violations = obligation_results.violations_count()
            delta_metrics = compute_delta(
                context.get("H_before", []),
                context.get("H_after", []),
                context.get("E_before", []),
                context.get("E_after", []),
                context.get("K_before", []),
                context.get("K_after", []),
                changed_paths=workspace.get_changed_files(),
                violations=violations,
            ).to_dict()

            justification = VJustification(
                time_ms=int((time.time() - start) * 1000),
                backtracks=context.get("backtracks", 0),
                audit_cost=violations * 1.0,
                tech_debt=violations,
                llm_time_ms=None,
                model=None,
            )

            result = {
                "success": obligation_results.all_passed(),
                "obligation_results": obligation_results,
                "violations": violations,
                "delta_metrics": delta_metrics,
                "justification": justification,
                "workspace_status": workspace.get_status(),
                "evaluation_time_ms": justification.time_ms,
                "obligation_details": get_obligation_details(workspace.work_dir),
                "violation_summary": get_violation_summary(obligation_results),
            }
            self._record_evaluation(patch_text, result)
            return result

    def batch_evaluate(
        self, patches: List[str], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        for index, patch in enumerate(patches):
            try:
                evaluation = self.evaluate_patch(patch, context)
                evaluation["patch_index"] = index
                results.append(evaluation)
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "success": False,
                        "error": f"Evaluation failed: {exc}",
                        "patch_index": index,
                        "evaluation_time_ms": 0,
                    }
                )
        return results

    def get_best_patch(
        self, patches: List[str], context: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        results = self.batch_evaluate(patches, context)
        best_score = -1.0
        best_index = -1
        for idx, result in enumerate(results):
            if result.get("success"):
                score = 1.0 - (
                    result.get("violations", 0) * 0.1
                    + result.get("delta_metrics", {}).get("delta_total", 1.0) * 0.5
                )
                if score > best_score:
                    best_score = score
                    best_index = idx
        if best_index >= 0:
            return best_index, results[best_index]
        return 0, results[0] if results else (-1, {})

    def get_evaluation_stats(self) -> Dict[str, Any]:
        if not self.evaluation_history:
            return {"total_evaluations": 0}
        total = len(self.evaluation_history)
        successes = sum(1 for item in self.evaluation_history if item["success"])
        return {
            "total_evaluations": total,
            "successful_evaluations": successes,
            "success_rate": successes / total if total else 0.0,
            "last_evaluation": self.evaluation_history[-1],
        }

    def clear_history(self) -> None:
        self.evaluation_history = []

    def _record_evaluation(self, patch_text: str, result: Dict[str, Any]) -> None:
        self.evaluation_history.append(
            {
                "patch_length": len(patch_text),
                "success": result.get("success", False),
                "violations": result.get("violations", 0),
                "delta_total": result.get("delta_metrics", {}).get("delta_total", 0.0),
                "evaluation_time_ms": result.get("evaluation_time_ms", 0),
            }
        )

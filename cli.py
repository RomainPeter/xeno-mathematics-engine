"""High-level orchestration entry point used in tests."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from core.pcap import merkle_of, now_iso, write_pcap
from controller.deterministic import DeterministicController
from generator.stochastic import StochasticGenerator
from metrics.collect import MetricsCollector
from metrics.report import ReportGenerator
from planner.meta import MetacognitivePlanner
from proofengine.core.schemas import ObligationResults, PCAP, VJustification, XState
from proofengine.core.state import create_initial_state
from verifier.runner import verify_pcap_dir


class ProofEngineOrchestrator:
    """Coordinates planning, generation, evaluation and reporting phases."""

    def __init__(self, base_dir: str = "demo_repo", output_dir: str = "out"):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.pcap_dir = f"{output_dir}/pcap"
        self.metrics_dir = f"{output_dir}/metrics"
        self.audit_dir = f"{output_dir}/audit"
        for path in (self.pcap_dir, self.metrics_dir, self.audit_dir):
            os.makedirs(path, exist_ok=True)

        self.planner = MetacognitivePlanner()
        self.generator = StochasticGenerator()
        self.controller = DeterministicController(base_dir)
        self.metrics_collector = MetricsCollector()
        self.report_generator = ReportGenerator()

        self.current_state: Optional[XState] = None
        self.execution_history: List[Dict[str, Any]] = []

    def run_demo(self, case_id: str = "demo_case", goal: Optional[str] = None) -> Dict[str, Any]:
        goal = goal or f"Improve {case_id}"
        start = time.time()
        self.current_state = self._create_initial_state(case_id, goal)

        planning = self._execute_planning_phase(goal)
        generation = self._execute_generation_phase(goal)
        verification = self._execute_verification_phase()
        metrics = self._execute_metrics_phase()

        success = generation.get("success", False)
        return {
            "success": success,
            "case_id": case_id,
            "goal": goal,
            "planning": planning,
            "generation": generation,
            "verification": verification,
            "metrics": metrics,
            "execution_time_ms": int((time.time() - start) * 1000),
        }

    def _create_initial_state(self, case_id: str, goal: str) -> XState:
        return create_initial_state(
            hypotheses={f"goal:{goal}"},
            evidences=set(),
            obligations=["tests_ok", "lint_ok", "types_ok", "security_ok", "complexity_ok", "docstring_ok"],
            artifacts=[],
            sigma={"case_id": case_id, "timestamp": now_iso()},
        )

    def _execute_planning_phase(self, goal: str) -> Dict[str, Any]:
        try:
            summary = json.dumps({"base_dir": self.base_dir, "goal": goal})
            plan = self.planner.propose_plan(goal, summary, self.current_state.K, self.execution_history)
            pcap = PCAP(
                operator="plan",
                case_id=self.current_state.Sigma.get("case_id", "unknown"),
                pre={"H": self.current_state.H, "K": self.current_state.K},
                post={"plan": plan.plan},
                obligations=self.current_state.K,
                justification=VJustification(time_ms=0, llm_time_ms=plan.llm_meta.get("latency_ms") if plan.llm_meta else 0, model=plan.llm_meta.get("model") if plan.llm_meta else None),
                proof_state_hash=merkle_of({"H": self.current_state.H, "K": self.current_state.K}),
                toolchain={"planner": "metacognitive"},
                llm_meta=plan.llm_meta,
                verdict="pass",
            )
            write_pcap(pcap, self.pcap_dir)
            self.execution_history.append({"operator": "plan", "verdict": "pass"})
            return {
                "success": True,
                "plan": plan.plan,
                "estimated_success": plan.est_success,
                "estimated_cost": plan.est_cost,
                "notes": plan.notes,
                "pcap_file": self.pcap_dir,
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "plan": [], "estimated_success": 0.0, "estimated_cost": 0.0}

    def _execute_generation_phase(self, goal: str) -> Dict[str, Any]:
        try:
            variants = self.generator.propose_variants(goal, json.dumps(self.current_state.K), self.current_state.K, k=3)
            best_patch = None
            best_result = None
            best_index = -1
            for idx, variant in enumerate(variants):
                evaluation = self.controller.evaluate_patch(variant.patch_unified, context={"H_before": list(self.current_state.H), "K_before": self.current_state.K})
                evaluation_for_hash = dict(evaluation)
                if isinstance(evaluation_for_hash.get("obligation_results"), ObligationResults):
                    evaluation_for_hash["obligation_results"] = evaluation_for_hash["obligation_results"].model_dump()
                if isinstance(evaluation_for_hash.get("justification"), VJustification):
                    evaluation_for_hash["justification"] = evaluation_for_hash["justification"].to_dict()
                pcap = PCAP(
                    operator="verify",
                    case_id=self.current_state.Sigma.get("case_id", "unknown"),
                    pre={"patch": variant.patch_unified[:120]},
                    post={"evaluation": evaluation},
                    obligations=self.current_state.K,
                    justification=_coerce_justification(evaluation.get("justification")),
                    proof_state_hash=merkle_of(evaluation_for_hash),
                    toolchain={"controller": "deterministic"},
                    llm_meta=_maybe_mapping(variant.llm_meta),
                    verdict="pass" if evaluation.get("success") else "fail",
                )
                write_pcap(pcap, self.pcap_dir)
                if evaluation.get("success") and (best_result is None or evaluation.get("violations", 0) < best_result.get("violations", 0)):
                    best_patch = variant
                    best_result = evaluation
                    best_index = idx
            if best_patch is None:
                return self._execute_rollback_phase(goal)
            return {
                "success": True,
                "best_patch": best_patch.patch_unified,
                "best_result": best_result,
                "best_index": best_index,
                "total_variants": len(variants),
                "violations": best_result.get("violations", 0),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "total_variants": 0}

    def _execute_rollback_phase(self, goal: str) -> Dict[str, Any]:
        try:
            pcap = PCAP(
                operator="rollback",
                case_id=self.current_state.Sigma.get("case_id", "unknown"),
                pre={"reason": "all variants failed"},
                post={"action": "replan"},
                obligations=self.current_state.K,
                justification=VJustification(backtracks=1),
                proof_state_hash=merkle_of({"rollback": True}),
                toolchain={"controller": "deterministic"},
                verdict="fail",
            )
            write_pcap(pcap, self.pcap_dir)
            replan = self.planner.replan_after_failure(goal, ["analyse", "retry"], "All variants failed", json.dumps(self.current_state.K), self.current_state.K, [])
            replan_pcap = PCAP(
                operator="replan",
                case_id=self.current_state.Sigma.get("case_id", "unknown"),
                pre={"failure": "all variants failed"},
                post={"new_plan": replan.plan},
                obligations=self.current_state.K,
                justification=VJustification(time_ms=0, llm_time_ms=replan.llm_meta.get("latency_ms") if replan.llm_meta else 0),
                proof_state_hash=merkle_of({"replan": True}),
                toolchain={"planner": "metacognitive"},
                llm_meta=replan.llm_meta,
                verdict="pass",
            )
            write_pcap(replan_pcap, self.pcap_dir)
            self.execution_history.append({"operator": "replan", "verdict": "pass"})
            return {"success": False, "rollback": True, "replan": replan.plan, "estimated_success": replan.est_success, "notes": replan.notes}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "rollback": True, "error": str(exc)}

    def _execute_verification_phase(self) -> Dict[str, Any]:
        try:
            result = verify_pcap_dir(self.pcap_dir, self.audit_dir)
            return {"success": True, "verification": result, "attestation_file": result.get("attestation_file")}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def _execute_metrics_phase(self) -> Dict[str, Any]:
        try:
            metrics = self.metrics_collector.collect_metrics(self.pcap_dir)
            markdown = self.report_generator.save_report(metrics, self.metrics_dir, "markdown")
            json_report = self.report_generator.save_report(metrics, self.metrics_dir, "json")
            return {"success": True, "metrics": metrics, "markdown_report": markdown, "json_report": json_report}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}


__all__ = ["ProofEngineOrchestrator"]


def _coerce_justification(value: Any) -> VJustification:
    if isinstance(value, VJustification):
        return value
    if isinstance(value, dict):
        return VJustification.model_validate(value)
    return VJustification()


def _maybe_mapping(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, dict):
        return value
    return None

"""
Hermetic OrchestratorLite for lab mode.

Runs AE then CEGIS with budgets/timeouts and structured event emissions,
without persisting PCAP/AuditPack (artifacts written via EventBus sinks only).
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from pefc.events.structured_bus import StructuredEventBus
from orchestrator.engines.ae_engine import AEEngine, AEContext
from orchestrator.engines.cegis_engine import CegisEngine, CegisContext, Verdict


@dataclass
class OrchestratorLiteConfig:
    ae_timeout: float = 10.0
    cegis_max_iterations: int = 3
    cegis_propose_timeout: float = 10.0
    cegis_verify_timeout: float = 10.0
    cegis_refine_timeout: float = 10.0


class OrchestratorLite:
    def __init__(
        self,
        config: OrchestratorLiteConfig,
        ae_engine: AEEngine,
        cegis_engine: CegisEngine,
        event_bus: StructuredEventBus,
    ) -> None:
        self.config = config
        self.ae_engine = ae_engine
        self.cegis_engine = cegis_engine
        self.event_bus = event_bus

        self.run_id = f"r-{uuid.uuid4().hex[:16]}"
        self.trace_id = f"t-{uuid.uuid4().hex[:16]}"

        # Metrics containers (lab-grade KPIs)
        self.metrics: Dict[str, Any] = {
            "ae": {
                "concepts_visited": 0,
                "closure_calls": 0,
                "avg_step_ms": 0.0,
                "steps": 0,
            },
            "cegis": {
                "proposals": 0,
                "accepts": 0,
                "patch_accept_rate": 0.0,
                "ce_found_count": 0,
                "verify_calls": 0,
                "verify_total_ms": 0.0,
                "mean_verify_ms": 0.0,
                "retries": 0,
            },
            "global": {
                "incidents_count": {},
                "pcap_count": 0,
            },
        }
        self._progress_series: list[float] = []  # scalar metric to detect no-progress/oscillation

    async def run(self, domain_spec: Dict[str, Any], budgets: Dict[str, Any]) -> Dict[str, Any]:
        # Event bus lifecycle
        self.event_bus.set_correlation_ids(self.trace_id, self.run_id)
        try:
            await self.event_bus.start()
        except Exception as e:
            import logging
            logging.warning(f"Failed to start event bus: {e}")

        self.event_bus.emit_orchestrator_event(
            "started",
            payload={"domain_spec": domain_spec, "budgets": budgets},
        )

        start_time = datetime.now()
        try:
            await self._initialize(domain_spec)
            await self._run_ae(domain_spec, budgets)
            await self._run_cegis(domain_spec, budgets)
            self.event_bus.emit_orchestrator_event(
                "completed",
                payload={"duration_s": (datetime.now() - start_time).total_seconds()},
            )
        except Exception as e:
            self.event_bus.emit_incident(
                incident_type="orchestrator_lite_failure",
                severity="error",
                context={"error": str(e)},
            )
            raise
        finally:
            # Snapshot metrics
            self.event_bus.emit(
                "Metrics.Snapshot",
                **self.metrics,
            )
            try:
                await self.event_bus.stop()
            except Exception as e:
                import logging
                logging.warning(f"Failed to stop event bus: {e}")
        return self.metrics

    async def _initialize(self, domain_spec: Dict[str, Any]) -> None:
        await asyncio.gather(
            self.ae_engine.initialize(domain_spec),
            self.cegis_engine.initialize(domain_spec),
        )

    async def _run_ae(self, domain_spec: Dict[str, Any], budgets: Dict[str, Any]) -> None:
        ctx = AEContext(
            run_id=self.run_id,
            step_id=f"s-ae-{uuid.uuid4().hex[:8]}",
            trace_id=self.trace_id,
            domain_spec=domain_spec,
            state={},
            budgets=budgets,
            thresholds={},
        )
        try:
            step_start = datetime.now()
            result = await asyncio.wait_for(
                self.ae_engine.next_closure_step(ctx), timeout=self.config.ae_timeout
            )
            elapsed_ms = (datetime.now() - step_start).total_seconds() * 1000.0
            # Update AE KPIs
            self.metrics["ae"]["steps"] += 1
            prev_avg = self.metrics["ae"]["avg_step_ms"]
            n = self.metrics["ae"]["steps"]
            self.metrics["ae"]["avg_step_ms"] = prev_avg + (elapsed_ms - prev_avg) / max(n, 1)
            concepts_count = 0
            if hasattr(result, "concepts") and isinstance(result.concepts, list):
                concepts_count = len(result.concepts)
            self.metrics["ae"]["concepts_visited"] += concepts_count
        except asyncio.TimeoutError:
            self.event_bus.emit(
                "Budget.Overrun",
                phase="AE",
                timeout=self.config.ae_timeout,
            )
            raise

    async def _run_cegis(self, domain_spec: Dict[str, Any], budgets: Dict[str, Any]) -> None:
        ctx = CegisContext(
            run_id=self.run_id,
            step_id=f"s-cegis-{uuid.uuid4().hex[:8]}",
            trace_id=self.trace_id,
            specification=domain_spec.get("specification", {}),
            constraints=domain_spec.get("constraints", []),
            budgets=budgets,
            state={},
        )

        max_iters = self.config.cegis_max_iterations
        time_budget = budgets.get("time_budget", None)
        run_start = datetime.now()
        epsilon = budgets.get("epsilon", 1e-9)
        no_progress_k = budgets.get("no_progress_k", 3)
        last_status: Optional[bool] = None
        oscillation_count = 0
        for iteration in range(max_iters):
            # Time budget stop
            if (
                time_budget is not None
                and (datetime.now() - run_start).total_seconds() > time_budget
            ):
                self.event_bus.emit(
                    "Budget.Overrun",
                    phase="CEGIS",
                    timeout=time_budget,
                )
                break
            candidate = await asyncio.wait_for(
                self.cegis_engine.propose(ctx),
                timeout=self.config.cegis_propose_timeout,
            )
            self.metrics["cegis"]["proposals"] += 1
            res = await asyncio.wait_for(
                self.cegis_engine.verify(candidate, ctx),
                timeout=self.config.cegis_verify_timeout,
            )
            # Track verify timing if available via budgets (not provided here); estimate from event bus would need subscriber.
            self.metrics["cegis"]["verify_calls"] += 1
            # Success
            if isinstance(res, Verdict) and res.valid:
                self.metrics["cegis"]["accepts"] += 1
                self.metrics["cegis"]["patch_accept_rate"] = self.metrics["cegis"]["accepts"] / max(
                    self.metrics["cegis"]["proposals"], 1
                )
                self._progress_series.append(self.metrics["cegis"]["patch_accept_rate"])
                # Oscillation detection (success after failure and vice-versa in alternance)
                status = True
                if last_status is not None and last_status != status:
                    oscillation_count += 1
                last_status = status
                return
            # Refine
            refined = await asyncio.wait_for(
                self.cegis_engine.refine(candidate, res, ctx),
                timeout=self.config.cegis_refine_timeout,
            )
            ctx.state["last_candidate"] = refined
            # Update KPIs for CE found
            try:
                # If res is a Counterexample-like, count it
                if hasattr(res, "failing_property"):
                    self.metrics["cegis"]["ce_found_count"] += 1
            except Exception as e:
                import logging
                logging.warning(f"Error updating CEGIS metrics: {e}")
            # Progress metric update (no-accept → rate unchanged)
            self._progress_series.append(self.metrics["cegis"]["patch_accept_rate"])
            # Oscillation detection
            status = False
            if last_status is not None and last_status != status:
                oscillation_count += 1
            last_status = status
            # No progress over k iters?
            if len(self._progress_series) >= no_progress_k:
                window = self._progress_series[-no_progress_k:]
                if max(window) - min(window) < epsilon:
                    self.event_bus.emit(
                        "Incident",
                        code="no_progress",
                        message="No progress over last iterations",
                        detail={"k": no_progress_k, "epsilon": epsilon},
                    )
                    # Update incidents counter
                    self.metrics["global"]["incidents_count"].setdefault("no_progress", 0)
                    self.metrics["global"]["incidents_count"]["no_progress"] += 1
                    break
            # Oscillation guard (simple heuristic)
            if oscillation_count >= 3:
                self.event_bus.emit(
                    "Incident",
                    code="oscillation_detected",
                    message="Oscillation detected in CEGIS convergence",
                    detail={"iterations": iteration + 1},
                )
                self.metrics["global"]["incidents_count"].setdefault("oscillation_detected", 0)
                self.metrics["global"]["incidents_count"]["oscillation_detected"] += 1
                break
        # Max iters reached
        self.event_bus.emit(
            "CEGIS.Iter.End",
            iterations=max_iters,
            reason="max_iters_reached",
        )
        self.metrics["global"]["incidents_count"].setdefault("max_iters_reached", 0)
        self.metrics["global"]["incidents_count"]["max_iters_reached"] += 1

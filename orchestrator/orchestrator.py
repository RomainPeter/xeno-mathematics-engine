"""
Main Orchestrator for Discovery Engine 2-Cat.
Coordinates AE and CEGIS engines with async scheduling and event publishing.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from .engines import (
    AEEngine,
    CegisEngine,
    AEContext,
    CegisContext,
    CegisResult,
    Verdict,
)
from .config import OrchestratorConfig
from .persistence import PCAPPersistence, IncidentPersistence, AuditPackBuilder
from ..pefc.events.structured_bus import StructuredEventBus
from ..pefc.pcap.model import PCAP
from ..pefc.incidents.types import Incident


@dataclass
class OrchestratorState:
    """Orchestrator runtime state."""

    run_id: str
    trace_id: str
    phase: str  # "ae" | "cegis" | "completed" | "failed"
    ae_results: List[Dict[str, Any]]
    cegis_results: List[Dict[str, Any]]
    incidents: List[Incident]
    pcaps: List[PCAP]
    metrics: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None


class Orchestrator:
    """Main orchestrator for AE/CEGIS pipeline."""

    def __init__(
        self,
        config: OrchestratorConfig,
        ae_engine: AEEngine,
        cegis_engine: CegisEngine,
        llm_adapter: Any,
        verifier: Any,
        event_bus: Optional[StructuredEventBus] = None,
    ):
        self.config = config
        self.ae_engine = ae_engine
        self.cegis_engine = cegis_engine
        self.llm_adapter = llm_adapter
        self.verifier = verifier
        self.event_bus = event_bus or StructuredEventBus()
        self.state: Optional[OrchestratorState] = None

        # Persistence components
        self.pcap_persistence = PCAPPersistence(config.audit_dir)
        self.incident_persistence = IncidentPersistence(config.audit_dir)
        self.audit_pack_builder = AuditPackBuilder(config.audit_dir)

    async def run(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> OrchestratorState:
        """
        Run the complete AE/CEGIS pipeline.

        Args:
            domain_spec: Domain specification
            budgets: Time and resource budgets
            thresholds: Success thresholds

        Returns:
            Final orchestrator state
        """
        # Initialize state
        self.state = OrchestratorState(
            run_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            phase="initializing",
            ae_results=[],
            cegis_results=[],
            incidents=[],
            pcaps=[],
            metrics={},
            start_time=datetime.now(),
        )

        # Set correlation IDs for structured events
        self.event_bus.set_correlation_ids(self.state.trace_id, self.state.run_id)

        # Start event bus drain loop to write events to sinks
        try:
            await self.event_bus.start()
        except Exception as e:
            # Non-fatal: continue without background drain
            import logging
            logging.warning(f"Failed to start event bus: {e}")

        # Emit start event
        self.event_bus.emit_orchestrator_event(
            "started",
            payload={
                "domain_spec": domain_spec,
                "budgets": budgets,
                "thresholds": thresholds,
            },
        )

        try:
            # Initialize engines
            await self._initialize_engines(domain_spec)

            # Run AE phase
            await self._run_ae_phase(domain_spec, budgets, thresholds)

            # Run CEGIS phase
            await self._run_cegis_phase(domain_spec, budgets, thresholds)

            # Complete
            self.state.phase = "completed"
            self.state.end_time = datetime.now()

            # Build audit pack
            audit_pack = await self.audit_pack_builder.build_audit_pack(
                self.state.run_id, self.state.metrics
            )

            self.event_bus.emit_orchestrator_event(
                "completed",
                payload={
                    "metrics": self.state.metrics,
                    "duration": (self.state.end_time - self.state.start_time).total_seconds(),
                    "audit_pack": audit_pack,
                },
            )

        except Exception as e:
            self.state.phase = "failed"
            self.state.end_time = datetime.now()

            # Create incident
            incident = Incident(
                id=str(uuid.uuid4()),
                type="orchestrator_failure",
                severity="critical",
                context={"error": str(e), "phase": self.state.phase},
                evidence_refs=[],
                obligations=[],
                V_target={},
            )
            self.state.incidents.append(incident)

            # Persist incident
            await self.incident_persistence.persist_incident(self.state.run_id, incident)

            self.event_bus.emit_incident(
                "orchestrator_failure",
                "critical",
                {"error": str(e), "phase": self.state.phase},
            )

            raise

        finally:
            # Cleanup engines
            await self._cleanup_engines()

            # Stop event bus (best-effort flush)
            try:
                await self.event_bus.stop()
            except Exception as e:
                import logging
                logging.warning(f"Failed to stop event bus: {e}")

        return self.state

    async def _initialize_engines(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize all engines."""
        self.event_bus.emit(
            "orchestrator.engines.initializing",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

        await asyncio.gather(
            self.ae_engine.initialize(domain_spec),
            self.cegis_engine.initialize(domain_spec),
        )

        self.event_bus.emit(
            "orchestrator.engines.initialized",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

    async def _run_ae_phase(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> None:
        """Run Attribute Exploration phase."""
        self.state.phase = "ae"

        self.event_bus.emit(
            "orchestrator.ae.started",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

        # Create AE context
        ae_ctx = AEContext(
            run_id=self.state.run_id,
            step_id=str(uuid.uuid4()),
            trace_id=self.state.trace_id,
            domain_spec=domain_spec,
            state={},
            budgets=budgets,
            thresholds=thresholds,
        )

        # Run AE with timeout and retries
        try:
            result = await asyncio.wait_for(
                self.ae_engine.next_closure_step(ae_ctx), timeout=self.config.ae_timeout
            )

            self.state.ae_results.append(result)

            self.event_bus.emit(
                "orchestrator.ae.completed",
                run_id=self.state.run_id,
                trace_id=self.state.trace_id,
                concepts_count=len(result.concepts),
                implications_count=len(result.implications),
            )

        except asyncio.TimeoutError:
            # Create timeout incident
            incident = Incident(
                id=str(uuid.uuid4()),
                type="ae_timeout",
                severity="high",
                context={"timeout": self.config.ae_timeout},
                evidence_refs=[],
                obligations=[],
                V_target={},
            )
            self.state.incidents.append(incident)

            self.event_bus.emit(
                "orchestrator.ae.timeout",
                run_id=self.state.run_id,
                trace_id=self.state.trace_id,
                timeout=self.config.ae_timeout,
            )

            raise

    async def _run_cegis_phase(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> None:
        """Run CEGIS phase."""
        self.state.phase = "cegis"

        self.event_bus.emit(
            "orchestrator.cegis.started",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

        # Create CEGIS context
        cegis_ctx = CegisContext(
            run_id=self.state.run_id,
            step_id=str(uuid.uuid4()),
            trace_id=self.state.trace_id,
            specification=domain_spec.get("specification", {}),
            constraints=domain_spec.get("constraints", []),
            budgets=budgets,
            state={},
        )

        # Run CEGIS loop
        max_iterations = self.config.cegis_max_iterations
        stable_no_improve = 0
        max_stable = self.config.cegis_max_stable_no_improve

        for iteration in range(max_iterations):
            try:
                # Propose candidate
                candidate = await asyncio.wait_for(
                    self.cegis_engine.propose(cegis_ctx),
                    timeout=self.config.cegis_propose_timeout,
                )

                # Verify candidate
                verification_result = await asyncio.wait_for(
                    self.cegis_engine.verify(candidate, cegis_ctx),
                    timeout=self.config.cegis_verify_timeout,
                )

                if isinstance(verification_result, Verdict) and verification_result.valid:
                    # Success - create result
                    result = CegisResult(
                        step_id=str(uuid.uuid4()),
                        success=True,
                        candidate=candidate,
                        verdict=verification_result,
                        counterexample=None,
                        metrics={"iterations": iteration + 1},
                        timings={},
                    )
                    self.state.cegis_results.append(result)

                    self.event_bus.emit(
                        "orchestrator.cegis.completed",
                        run_id=self.state.run_id,
                        trace_id=self.state.trace_id,
                        iterations=iteration + 1,
                        candidate_id=candidate.id,
                    )
                    break

                else:
                    # Counterexample - refine
                    counterexample = verification_result
                    refined_candidate = await asyncio.wait_for(
                        self.cegis_engine.refine(candidate, counterexample, cegis_ctx),
                        timeout=self.config.cegis_refine_timeout,
                    )

                    # Update context for next iteration
                    cegis_ctx.state["last_candidate"] = refined_candidate
                    cegis_ctx.state["last_counterexample"] = counterexample

                    stable_no_improve += 1

                    self.event_bus.emit(
                        "orchestrator.cegis.refined",
                        run_id=self.state.run_id,
                        trace_id=self.state.trace_id,
                        iteration=iteration + 1,
                        counterexample_id=counterexample.id,
                    )

                    if stable_no_improve >= max_stable:
                        # Create stability incident
                        incident = Incident(
                            id=str(uuid.uuid4()),
                            type="cegis_stability",
                            severity="medium",
                            context={"stable_iterations": stable_no_improve},
                            evidence_refs=[],
                            obligations=[],
                            V_target={},
                        )
                        self.state.incidents.append(incident)
                        break

            except asyncio.TimeoutError:
                # Create timeout incident
                incident = Incident(
                    id=str(uuid.uuid4()),
                    type="cegis_timeout",
                    severity="high",
                    context={
                        "iteration": iteration,
                        "timeout": self.config.cegis_propose_timeout,
                    },
                    evidence_refs=[],
                    obligations=[],
                    V_target={},
                )
                self.state.incidents.append(incident)
                break

        self.event_bus.emit(
            "orchestrator.cegis.completed",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
            iterations=len(self.state.cegis_results),
            incidents=len(self.state.incidents),
        )

    async def _cleanup_engines(self) -> None:
        """Cleanup all engines."""
        self.event_bus.emit(
            "orchestrator.engines.cleaning",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

        await asyncio.gather(self.ae_engine.cleanup(), self.cegis_engine.cleanup())

        self.event_bus.emit(
            "orchestrator.engines.cleaned",
            run_id=self.state.run_id,
            trace_id=self.state.trace_id,
        )

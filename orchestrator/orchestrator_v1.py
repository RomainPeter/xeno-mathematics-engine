"""
Orchestrator v1 with real components.
Replaces all mocks with actual engines, adapters, and schedulers.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from .engines.real_ae_engine import RealAEEngine
from .engines.real_cegis_engine import RealCegisEngine
from .adapters.llm_adapter import LLMAdapter
from .adapters.verifier import Verifier
from .scheduler.async_scheduler import AsyncScheduler
from .scheduler.budget_manager import BudgetManager
from .incidents.failreason import FailReasonFactory
from .config import OrchestratorConfig
from .persistence import PCAPPersistence, IncidentPersistence, AuditPackBuilder
from ..pefc.events.structured_bus import StructuredEventBus
from ..pefc.pcap.model import PCAP
from ..pefc.incidents.types import Incident


@dataclass
class OrchestratorV1Config(OrchestratorConfig):
    """Configuration for Orchestrator v1."""

    # Real component settings
    enable_budget_management: bool = True
    enable_async_scheduler: bool = True
    enable_failreason_emission: bool = True

    # LLM settings
    llm_api_url: str = "https://api.openai.com/v1/chat/completions"
    llm_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1

    # Verifier settings
    verifier_timeout: float = 20.0
    verifier_tools: List[str] = None

    # Scheduler settings
    max_concurrent_tasks: int = 10
    scheduler_timeout: float = 30.0

    # Budget settings
    budget_warning_threshold: float = 0.8
    budget_critical_threshold: float = 0.95
    budget_overrun_threshold: float = 1.0


@dataclass
class OrchestratorV1State:
    """Orchestrator v1 runtime state."""

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

    # V1 specific
    budget_status: Dict[str, Any] = None
    scheduler_status: Dict[str, Any] = None
    failreasons: List[Dict[str, Any]] = None


class OrchestratorV1:
    """Orchestrator v1 with real components."""

    def __init__(
        self,
        config: OrchestratorV1Config,
        ae_engine: RealAEEngine,
        cegis_engine: RealCegisEngine,
        llm_adapter: LLMAdapter,
        verifier: Verifier,
        scheduler: AsyncScheduler,
        budget_manager: BudgetManager,
        event_bus: StructuredEventBus,
    ):
        self.config = config
        self.ae_engine = ae_engine
        self.cegis_engine = cegis_engine
        self.llm_adapter = llm_adapter
        self.verifier = verifier
        self.scheduler = scheduler
        self.budget_manager = budget_manager
        self.event_bus = event_bus
        self.state: Optional[OrchestratorV1State] = None

        # Persistence components
        self.pcap_persistence = PCAPPersistence(config.audit_dir)
        self.incident_persistence = IncidentPersistence(config.audit_dir)
        self.audit_pack_builder = AuditPackBuilder(config.audit_dir)

        # Initialize components
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Setup event handlers for real components."""
        # Budget warning handler
        if self.config.enable_budget_management:
            self.budget_manager.add_warning_callback(self._handle_budget_warning)
            self.budget_manager.add_overrun_callback(self._handle_budget_overrun)

    async def run(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> OrchestratorV1State:
        """Run the complete Orchestrator v1 pipeline."""
        # Initialize state
        self.state = OrchestratorV1State(
            run_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            phase="initializing",
            ae_results=[],
            cegis_results=[],
            incidents=[],
            pcaps=[],
            metrics={},
            start_time=datetime.now(),
            failreasons=[],
        )

        # Set correlation IDs for structured events
        self.event_bus.set_correlation_ids(self.state.trace_id, self.state.run_id)

        # Emit start event
        self.event_bus.emit_orchestrator_event(
            "started",
            payload={
                "domain_spec": domain_spec,
                "budgets": budgets,
                "thresholds": thresholds,
                "version": "v1",
            },
        )

        try:
            # Initialize all components
            await self._initialize_components(domain_spec)

            # Set budgets
            if self.config.enable_budget_management:
                await self.budget_manager.set_budget(budgets)

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
                    "version": "v1",
                },
            )

        except Exception as e:
            self.state.phase = "failed"
            self.state.end_time = datetime.now()

            # Create incident
            incident = Incident(
                id=str(uuid.uuid4()),
                type="orchestrator_v1_failure",
                severity="critical",
                context={"error": str(e), "phase": self.state.phase, "version": "v1"},
                evidence_refs=[],
                obligations=[],
                V_target={},
            )
            self.state.incidents.append(incident)

            # Persist incident
            await self.incident_persistence.persist_incident(self.state.run_id, incident)

            # Emit FailReason
            if self.config.enable_failreason_emission:
                await self.emit_failreason(
                    FailReasonFactory.create_unknown_error(
                        component="orchestrator_v1", operation="run", error=str(e)
                    )
                )

            self.event_bus.emit_orchestrator_event(
                "failed",
                payload={"error": str(e), "phase": self.state.phase, "version": "v1"},
            )

            raise

        finally:
            # Cleanup components
            await self._cleanup_components()

        return self.state

    async def _initialize_components(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize all real components."""
        self.event_bus.emit_orchestrator_event(
            "components.initializing", payload={"domain_spec": domain_spec}
        )

        # Initialize engines
        await asyncio.gather(
            self.ae_engine.initialize(domain_spec),
            self.cegis_engine.initialize(domain_spec),
        )

        # Initialize adapters
        await asyncio.gather(
            self.llm_adapter.initialize(domain_spec),
            self.verifier.initialize(domain_spec),
        )

        # Initialize scheduler
        if self.config.enable_async_scheduler:
            await self.scheduler.start()

        # Initialize budget manager
        if self.config.enable_budget_management:
            await self.budget_manager.start()

        self.event_bus.emit_orchestrator_event(
            "components.initialized",
            payload={
                "components": [
                    "ae_engine",
                    "cegis_engine",
                    "llm_adapter",
                    "verifier",
                    "scheduler",
                    "budget_manager",
                ]
            },
        )

    async def _run_ae_phase(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> None:
        """Run Attribute Exploration phase with real engine."""
        self.state.phase = "ae"

        self.event_bus.emit_ae_event(
            "started", payload={"domain_spec": domain_spec, "budgets": budgets}
        )

        try:
            # Create AE context
            from .engines.ae_engine import AEContext

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
            result = await asyncio.wait_for(
                self.ae_engine.next_closure_step(ae_ctx), timeout=self.config.ae_timeout
            )

            self.state.ae_results.append(result)

            # Emit PCAP if successful
            if result.success:
                await self._emit_pcap("ae_concept_generated", result)

            self.event_bus.emit_ae_event(
                "completed",
                payload={
                    "concepts_count": len(result.concepts),
                    "implications_count": len(result.implications),
                    "success": result.success,
                },
            )

        except asyncio.TimeoutError:
            # Create timeout incident
            incident = Incident(
                id=str(uuid.uuid4()),
                type="ae_timeout",
                severity="high",
                context={"timeout": self.config.ae_timeout, "phase": "ae"},
                evidence_refs=[],
                obligations=[],
                V_target={},
            )
            self.state.incidents.append(incident)

            # Persist incident
            await self.incident_persistence.persist_incident(self.state.run_id, incident)

            # Emit FailReason
            if self.config.enable_failreason_emission:
                await self.emit_failreason(
                    FailReasonFactory.create_timeout_exceeded(
                        component="ae_engine",
                        operation="next_closure_step",
                        timeout_duration=self.config.ae_timeout,
                    )
                )

            self.event_bus.emit_ae_event("timeout", payload={"timeout": self.config.ae_timeout})

            raise

    async def _run_cegis_phase(
        self,
        domain_spec: Dict[str, Any],
        budgets: Dict[str, Any],
        thresholds: Dict[str, Any],
    ) -> None:
        """Run CEGIS phase with real engine."""
        self.state.phase = "cegis"

        self.event_bus.emit_cegis_event(
            "started", payload={"domain_spec": domain_spec, "budgets": budgets}
        )

        # Create CEGIS context
        from .engines.cegis_engine import CegisContext

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

                if hasattr(verification_result, "valid") and verification_result.valid:
                    # Success - create result
                    from .engines.cegis_engine import CegisResult

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

                    # Emit PCAP
                    await self._emit_pcap("cegis_candidate_verified", result)

                    self.event_bus.emit_cegis_event(
                        "completed",
                        payload={
                            "iterations": iteration + 1,
                            "candidate_id": candidate.id,
                            "success": True,
                        },
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

                    self.event_bus.emit_cegis_event(
                        "refined",
                        payload={
                            "iteration": iteration + 1,
                            "counterexample_id": counterexample.id,
                            "stable_no_improve": stable_no_improve,
                        },
                    )

                    if stable_no_improve >= max_stable:
                        # Create stability incident
                        incident = Incident(
                            id=str(uuid.uuid4()),
                            type="cegis_stability",
                            severity="medium",
                            context={
                                "stable_iterations": stable_no_improve,
                                "phase": "cegis",
                            },
                            evidence_refs=[],
                            obligations=[],
                            V_target={},
                        )
                        self.state.incidents.append(incident)

                        # Persist incident
                        await self.incident_persistence.persist_incident(
                            self.state.run_id, incident
                        )

                        # Emit FailReason
                        if self.config.enable_failreason_emission:
                            await self.emit_failreason(
                                FailReasonFactory.create_max_iters_reached(
                                    component="cegis_engine",
                                    operation="refine",
                                    current_iters=iteration + 1,
                                    max_iters=max_iterations,
                                )
                            )
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
                        "phase": "cegis",
                    },
                    evidence_refs=[],
                    obligations=[],
                    V_target={},
                )
                self.state.incidents.append(incident)

                # Persist incident
                await self.incident_persistence.persist_incident(self.state.run_id, incident)

                # Emit FailReason
                if self.config.enable_failreason_emission:
                    await self.emit_failreason(
                        FailReasonFactory.create_timeout_exceeded(
                            component="cegis_engine",
                            operation="propose",
                            timeout_duration=self.config.cegis_propose_timeout,
                        )
                    )
                break

        self.event_bus.emit_cegis_event(
            "completed",
            payload={
                "iterations": len(self.state.cegis_results),
                "incidents": len(self.state.incidents),
            },
        )

    async def _emit_pcap(self, action: str, result: Any) -> None:
        """Emit PCAP for result."""
        pcap = PCAP(
            action=action,
            context_hash=str(hash(str(result))),
            obligations=[],
            justification={"metrics": result.metrics if hasattr(result, "metrics") else {}},
            proofs=[],
            meta={
                "result_type": type(result).__name__,
                "timestamp": datetime.now().isoformat(),
            },
        )

        self.state.pcaps.append(pcap)

        # Persist PCAP
        await self.pcap_persistence.persist_pcap(self.state.run_id, pcap)

        # Emit event
        self.event_bus.emit_pcap(pcap.dict())

    async def emit_failreason(self, failreason) -> None:
        """Emit FailReason."""
        self.state.failreasons.append(failreason.to_dict())

        # Emit event
        self.event_bus.emit_incident(
            "failreason_emitted", failreason.severity.value, failreason.context
        )

    async def _handle_budget_warning(self, budget_type, status, operation) -> None:
        """Handle budget warning."""
        self.event_bus.emit_budget_warning(budget_type.value, status.current, status.limit)

    async def _handle_budget_overrun(self, budget_type, status, operation) -> None:
        """Handle budget overrun."""
        self.event_bus.emit_budget_overrun(budget_type.value, status.current, status.limit)

        # Create incident
        incident = Incident(
            id=str(uuid.uuid4()),
            type="budget_overrun",
            severity="critical",
            context={
                "budget_type": budget_type.value,
                "current": status.current,
                "limit": status.limit,
                "overrun": status.current - status.limit,
            },
            evidence_refs=[],
            obligations=[],
            V_target={},
        )
        self.state.incidents.append(incident)

        # Persist incident
        await self.incident_persistence.persist_incident(self.state.run_id, incident)

    async def _cleanup_components(self) -> None:
        """Cleanup all components."""
        self.event_bus.emit_orchestrator_event("components.cleaning", payload={})

        # Cleanup engines
        await asyncio.gather(self.ae_engine.cleanup(), self.cegis_engine.cleanup())

        # Cleanup adapters
        await asyncio.gather(self.llm_adapter.cleanup(), self.verifier.cleanup())

        # Cleanup scheduler
        if self.config.enable_async_scheduler:
            await self.scheduler.stop()

        # Cleanup budget manager
        if self.config.enable_budget_management:
            await self.budget_manager.stop()

        self.event_bus.emit_orchestrator_event("components.cleaned", payload={})

    async def cleanup(self) -> None:
        """Cleanup orchestrator."""
        await self._cleanup_components()

        if self.budget_manager:
            await self.budget_manager.cleanup()

        if self.scheduler:
            await self.scheduler.cleanup()

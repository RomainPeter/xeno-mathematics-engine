"""
CEGIS Engine for code compliance.
Implements concurrent propose and verify with convergence testing.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .proposer import ProposalEngine
from .refiner import RefinementContext, RefinementEngine
from .types import (
    Candidate,
    CodeSnippet,
    ComplianceResult,
    ComplianceStatus,
    Counterexample,
    Proof,
    Verdict,
)
from .verifier import ComplianceVerifier, VerificationContext


class CEGISMode(Enum):
    """CEGIS execution modes."""

    STUB_ONLY = "stub_only"  # Deterministic mode
    HYBRID = "hybrid"  # LLM mockable mode
    FULL_LLM = "full_llm"  # Full LLM mode


@dataclass
class CEGISConfig:
    """Configuration for CEGIS engine."""

    max_iterations: int = 5
    timeout_per_iteration: float = 30.0
    mode: CEGISMode = CEGISMode.STUB_ONLY
    enable_concurrency: bool = True
    enable_pcap_emission: bool = True
    convergence_threshold: float = 0.95
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CEGISResult:
    """Result of CEGIS execution."""

    success: bool
    final_candidate: Optional[Candidate]
    iterations: int
    convergence_time: float
    counterexamples: List[Counterexample]
    pcap_emissions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_converged(self) -> bool:
        """Check if CEGIS converged."""
        return self.success and self.final_candidate is not None

    @property
    def convergence_rate(self) -> float:
        """Get convergence rate."""
        if self.iterations == 0:
            return 0.0
        return 1.0 / self.iterations if self.success else 0.0


class CEGISEngine:
    """Main CEGIS engine for code compliance."""

    def __init__(self, config: Optional[CEGISConfig] = None):
        self.config = config or CEGISConfig()
        self.proposal_engine = ProposalEngine()
        self.verifier = ComplianceVerifier()
        self.refiner = RefinementEngine()
        self.execution_history: List[Dict[str, Any]] = []
        self.pcap_emissions: List[Dict[str, Any]] = []

    async def execute_cegis(
        self, code_snippet: CodeSnippet, violation_type: str, rule_id: str, seed: str
    ) -> CEGISResult:
        """Execute CEGIS algorithm."""
        start_time = time.time()

        try:
            # Initialize
            current_candidate = None
            all_counterexamples = []
            iteration = 0

            # CEGIS loop
            while iteration < self.config.max_iterations:
                iteration_start = time.time()

                # Phase 1: Propose (if not first iteration)
                if iteration == 0:
                    # Initial proposal
                    current_candidate = await self._propose_initial(
                        code_snippet, violation_type, rule_id, seed
                    )
                else:
                    # Refine based on counterexamples
                    current_candidate = await self._refine_candidate(
                        current_candidate, all_counterexamples, iteration
                    )

                # Phase 2: Verify
                verification_result = await self._verify_candidate(
                    current_candidate, code_snippet, rule_id
                )

                # Check convergence
                if verification_result.is_compliant:
                    # Success - converged
                    convergence_time = time.time() - start_time

                    # Emit final PCAP
                    if self.config.enable_pcap_emission:
                        await self._emit_pcap(
                            current_candidate,
                            verification_result,
                            iteration,
                            "converged",
                        )

                    return CEGISResult(
                        success=True,
                        final_candidate=current_candidate,
                        iterations=iteration + 1,
                        convergence_time=convergence_time,
                        counterexamples=all_counterexamples,
                        pcap_emissions=self.pcap_emissions.copy(),
                        metadata={"convergence_reason": "compliant"},
                    )

                # Collect counterexamples
                new_counterexamples = verification_result.counterexamples
                all_counterexamples.extend(new_counterexamples)

                # Emit PCAP for this iteration
                if self.config.enable_pcap_emission:
                    await self._emit_pcap(
                        current_candidate, verification_result, iteration, "iteration"
                    )

                # Record execution
                execution_record = {
                    "iteration": iteration,
                    "candidate_id": current_candidate.id,
                    "verification_result": verification_result.to_dict(),
                    "counterexamples_count": len(new_counterexamples),
                    "execution_time": time.time() - iteration_start,
                }
                self.execution_history.append(execution_record)

                iteration += 1

            # Max iterations reached
            convergence_time = time.time() - start_time

            return CEGISResult(
                success=False,
                final_candidate=current_candidate,
                iterations=iteration,
                convergence_time=convergence_time,
                counterexamples=all_counterexamples,
                pcap_emissions=self.pcap_emissions.copy(),
                metadata={"convergence_reason": "max_iterations_reached"},
            )

        except Exception as e:
            # Error case
            convergence_time = time.time() - start_time

            return CEGISResult(
                success=False,
                final_candidate=current_candidate,
                iterations=iteration,
                convergence_time=convergence_time,
                counterexamples=all_counterexamples,
                pcap_emissions=self.pcap_emissions.copy(),
                metadata={"convergence_reason": "error", "error": str(e)},
            )

    async def _propose_initial(
        self, code_snippet: CodeSnippet, violation_type: str, rule_id: str, seed: str
    ) -> Candidate:
        """Propose initial candidate."""
        if self.config.mode == CEGISMode.STUB_ONLY:
            # Deterministic proposal
            return self.proposal_engine.propose(code_snippet, violation_type, rule_id, seed)
        else:
            # LLM-based proposal
            return await self._llm_propose(code_snippet, violation_type, rule_id, seed)

    async def _refine_candidate(
        self,
        candidate: Candidate,
        counterexamples: List[Counterexample],
        iteration: int,
    ) -> Candidate:
        """Refine candidate based on counterexamples."""
        if not counterexamples:
            return candidate

        # Create refinement context
        context = RefinementContext(
            original_candidate=candidate,
            counterexamples=counterexamples,
            iteration=iteration,
            max_iterations=self.config.max_iterations,
        )

        # Refine candidate
        refined_candidate = self.refiner.refine(context)

        return refined_candidate

    async def _verify_candidate(
        self, candidate: Candidate, code_snippet: CodeSnippet, rule_id: str
    ) -> ComplianceResult:
        """Verify candidate compliance."""
        # Create verification context
        verification_context = VerificationContext(
            candidate=candidate,
            original_code=code_snippet.content,
            file_path="generated.py",
            rule_id=rule_id,
        )

        # Verify compliance
        result = self.verifier.verify(verification_context)

        return result

    async def _llm_propose(
        self, code_snippet: CodeSnippet, violation_type: str, rule_id: str, seed: str
    ) -> Candidate:
        """LLM-based proposal (mockable for testing)."""
        # In real implementation, this would call an LLM
        # For now, use deterministic fallback
        return self.proposal_engine.propose(code_snippet, violation_type, rule_id, seed)

    async def _emit_pcap(
        self,
        candidate: Candidate,
        verification_result: ComplianceResult,
        iteration: int,
        status: str,
    ) -> None:
        """Emit PCAP for this iteration."""
        pcap = {
            "iteration": iteration,
            "candidate_id": candidate.id,
            "status": status,
            "verification_result": verification_result.to_dict(),
            "timestamp": time.time(),
            "metadata": {
                "rule_id": candidate.metadata.get("rule_id", "unknown"),
                "violation_type": candidate.metadata.get("violation_type", "unknown"),
            },
        }

        self.pcap_emissions.append(pcap)

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_iterations": 0, "average_time": 0.0}

        total_iterations = len(self.execution_history)
        total_time = sum(record["execution_time"] for record in self.execution_history)
        average_time = total_time / total_iterations

        return {
            "total_iterations": total_iterations,
            "total_time": total_time,
            "average_time": average_time,
            "proposal_statistics": self.proposal_engine.get_statistics(),
            "verification_statistics": self.verifier.get_statistics(),
            "refinement_statistics": self.refiner.get_statistics(),
        }

    def reset(self):
        """Reset engine state."""
        self.execution_history.clear()
        self.pcap_emissions.clear()
        self.proposal_engine.clear_history()
        self.verifier.reset()
        self.refiner.clear_history()


class ConcurrentCEGISEngine(CEGISEngine):
    """CEGIS engine with concurrent execution."""

    def __init__(self, config: Optional[CEGISConfig] = None):
        super().__init__(config)
        self.task_manager = asyncio.TaskGroup() if hasattr(asyncio, "TaskGroup") else None

    async def execute_cegis_concurrent(
        self, code_snippet: CodeSnippet, violation_type: str, rule_id: str, seed: str
    ) -> CEGISResult:
        """Execute CEGIS with concurrent propose and verify."""
        if not self.config.enable_concurrency:
            return await self.execute_cegis(code_snippet, violation_type, rule_id, seed)

        start_time = time.time()

        try:
            # Initialize
            current_candidate = None
            all_counterexamples = []
            iteration = 0

            # CEGIS loop with concurrency
            while iteration < self.config.max_iterations:
                iteration_start = time.time()

                # Concurrent propose and verify
                if iteration == 0:
                    # Initial proposal
                    current_candidate = await self._propose_initial(
                        code_snippet, violation_type, rule_id, seed
                    )
                else:
                    # Refine based on counterexamples
                    current_candidate = await self._refine_candidate(
                        current_candidate, all_counterexamples, iteration
                    )

                # Concurrent verification
                verification_tasks = []

                # Static analysis task
                static_task = asyncio.create_task(
                    self._verify_static_analysis(current_candidate, code_snippet, rule_id)
                )
                verification_tasks.append(static_task)

                # Unit test task
                test_task = asyncio.create_task(
                    self._verify_unit_test(current_candidate, code_snippet, rule_id)
                )
                verification_tasks.append(test_task)

                # Wait for all verification tasks
                verification_results = await asyncio.gather(*verification_tasks)

                # Combine results
                combined_result = self._combine_verification_results(verification_results)

                # Check convergence
                if combined_result.is_compliant:
                    # Success - converged
                    convergence_time = time.time() - start_time

                    # Emit final PCAP
                    if self.config.enable_pcap_emission:
                        await self._emit_pcap(
                            current_candidate, combined_result, iteration, "converged"
                        )

                    return CEGISResult(
                        success=True,
                        final_candidate=current_candidate,
                        iterations=iteration + 1,
                        convergence_time=convergence_time,
                        counterexamples=all_counterexamples,
                        pcap_emissions=self.pcap_emissions.copy(),
                        metadata={
                            "convergence_reason": "compliant",
                            "concurrent": True,
                        },
                    )

                # Collect counterexamples
                new_counterexamples = combined_result.counterexamples
                all_counterexamples.extend(new_counterexamples)

                # Emit PCAP for this iteration
                if self.config.enable_pcap_emission:
                    await self._emit_pcap(
                        current_candidate, combined_result, iteration, "iteration"
                    )

                # Record execution
                execution_record = {
                    "iteration": iteration,
                    "candidate_id": current_candidate.id,
                    "verification_result": combined_result.to_dict(),
                    "counterexamples_count": len(new_counterexamples),
                    "execution_time": time.time() - iteration_start,
                    "concurrent": True,
                }
                self.execution_history.append(execution_record)

                iteration += 1

            # Max iterations reached
            convergence_time = time.time() - start_time

            return CEGISResult(
                success=False,
                final_candidate=current_candidate,
                iterations=iteration,
                convergence_time=convergence_time,
                counterexamples=all_counterexamples,
                pcap_emissions=self.pcap_emissions.copy(),
                metadata={
                    "convergence_reason": "max_iterations_reached",
                    "concurrent": True,
                },
            )

        except Exception as e:
            # Error case
            convergence_time = time.time() - start_time

            return CEGISResult(
                success=False,
                final_candidate=current_candidate,
                iterations=iteration,
                convergence_time=convergence_time,
                counterexamples=all_counterexamples,
                pcap_emissions=self.pcap_emissions.copy(),
                metadata={
                    "convergence_reason": "error",
                    "error": str(e),
                    "concurrent": True,
                },
            )

    async def _verify_static_analysis(
        self, candidate: Candidate, code_snippet: CodeSnippet, rule_id: str
    ) -> ComplianceResult:
        """Verify using static analysis."""
        # Create verification context
        # NOTE: context variable used in static analysis verification

        # Run static analysis only
        violations = self.verifier.static_analyzer.analyze(candidate.patch, "generated.py")

        if not violations:
            verdict = Verdict(
                status=ComplianceStatus.OK,
                proofs=[
                    Proof(
                        rule_id=rule_id,
                        status=ComplianceStatus.OK,
                        evidence="Static analysis passed",
                        confidence=1.0,
                    )
                ],
            )
        else:
            verdict = Verdict(
                status=ComplianceStatus.VIOLATION,
                proofs=[
                    Proof(
                        rule_id=rule_id,
                        status=ComplianceStatus.VIOLATION,
                        evidence="Static analysis failed",
                        confidence=0.8,
                    )
                ],
            )

        return ComplianceResult(verdict=verdict, counterexamples=violations)

    async def _verify_unit_test(
        self, candidate: Candidate, code_snippet: CodeSnippet, rule_id: str
    ) -> ComplianceResult:
        """Verify using unit test."""
        # Generate and run unit test
        test_code = self.verifier.test_generator.generate_test(candidate, rule_id)
        test_result = self.verifier.test_runner.run_test(test_code)

        if test_result["success"]:
            verdict = Verdict(
                status=ComplianceStatus.OK,
                proofs=[
                    Proof(
                        rule_id=rule_id,
                        status=ComplianceStatus.OK,
                        evidence="Unit test passed",
                        confidence=1.0,
                    )
                ],
            )
        else:
            verdict = Verdict(
                status=ComplianceStatus.VIOLATION,
                proofs=[
                    Proof(
                        rule_id=rule_id,
                        status=ComplianceStatus.VIOLATION,
                        evidence="Unit test failed",
                        confidence=0.8,
                    )
                ],
            )

        return ComplianceResult(verdict=verdict, counterexamples=[])

    def _combine_verification_results(self, results: List[ComplianceResult]) -> ComplianceResult:
        """Combine multiple verification results."""
        if not results:
            return ComplianceResult(
                verdict=Verdict(status=ComplianceStatus.ERROR), counterexamples=[]
            )

        # Combine all counterexamples
        all_counterexamples = []
        for result in results:
            all_counterexamples.extend(result.counterexamples)

        # Determine overall status
        if all(result.is_compliant for result in results):
            overall_status = ComplianceStatus.OK
        else:
            overall_status = ComplianceStatus.VIOLATION

        # Combine proofs
        all_proofs = []
        for result in results:
            all_proofs.extend(result.verdict.proofs)

        verdict = Verdict(status=overall_status, proofs=all_proofs)

        return ComplianceResult(verdict=verdict, counterexamples=all_counterexamples)

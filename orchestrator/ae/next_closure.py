"""
Next-Closure algorithm for Attribute Exploration.
Implements the core AE loop with implication generation and verification.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from ..state import XState
from .oracle import Oracle, OracleResult


@dataclass
class Implication:
    """An implication A ⇒ B."""

    premises: List[str]
    conclusions: List[str]
    confidence: float
    source: str
    diversity_key: str
    costs: Dict[str, float]
    obligations: List[str]
    proofs: List[str]


class AEExplorer:
    """Attribute Exploration using Next-Closure algorithm."""

    def __init__(self, oracle: Oracle, state: XState):
        self.oracle = oracle
        self.state = state
        self.exploration_history: List[Dict[str, Any]] = []

    async def propose(self, k: int = 5) -> List[Implication]:
        """
        Propose k candidate implications.

        Args:
            k: Number of implications to generate

        Returns:
            List of candidate implications
        """
        # Generate implications using LLM prompts (stub)
        implications = []

        for i in range(k):
            # Simple implication generation based on current state
            implication = await self._generate_implication(i)
            implications.append(implication)

        return implications

    async def verify(self, implication: Implication) -> OracleResult:
        """
        Verify an implication using the oracle.

        Args:
            implication: Implication to verify

        Returns:
            OracleResult with verification outcome
        """
        impl_dict = {
            "premises": implication.premises,
            "conclusions": implication.conclusions,
        }

        result = await self.oracle.verify_implication(impl_dict)
        return result

    async def incorporate_valid(self, implication: Implication) -> str:
        """
        Incorporate a valid implication into the state.

        Args:
            implication: Valid implication to incorporate

        Returns:
            ID of the incorporated implication
        """
        impl_dict = {
            "premises": implication.premises,
            "conclusions": implication.conclusions,
            "confidence": implication.confidence,
            "source": implication.source,
            "costs": implication.costs,
            "obligations": implication.obligations,
            "proofs": implication.proofs,
        }

        impl_id = self.state.add_implication(impl_dict)

        # Update exploration history
        self.exploration_history.append(
            {
                "type": "implication_accepted",
                "id": impl_id,
                "implication": impl_dict,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return impl_id

    async def incorporate_counterexample(
        self, implication: Implication, counterexample: Dict[str, Any]
    ) -> str:
        """
        Incorporate a counterexample and update constraints.

        Args:
            implication: Failed implication
            counterexample: Counterexample that violated the implication

        Returns:
            ID of the counterexample
        """
        cex_id = self.state.add_counterexample(counterexample)

        # Update exploration history
        self.exploration_history.append(
            {
                "type": "counterexample_added",
                "id": cex_id,
                "implication": {
                    "premises": implication.premises,
                    "conclusions": implication.conclusions,
                },
                "counterexample": counterexample,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return cex_id

    async def run_until_closed(
        self, budgets_V: Dict[str, float], thresholds: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Run AE exploration until closure or budget exhausted.

        Args:
            budgets_V: Budget constraints (time_ms, audit_cost, etc.)
            thresholds: Convergence thresholds

        Returns:
            Exploration results
        """
        results = {
            "implications_accepted": [],
            "implications_rejected": [],
            "counterexamples": [],
            "final_state": None,
            "exploration_time": 0,
            "merkle_root": None,
        }

        start_time = datetime.now()
        iteration = 0
        max_iterations = 10  # Prevent infinite loops

        while iteration < max_iterations:
            print(f"AE iteration {iteration}")

            # Generate candidate implications
            candidates = await self.propose(k=3)

            for candidate in candidates:
                # Verify implication
                verification = await self.verify(candidate)

                if verification.valid:
                    # Incorporate valid implication
                    impl_id = await self.incorporate_valid(candidate)
                    results["implications_accepted"].append(impl_id)
                    print(
                        f"✅ Accepted implication: {candidate.premises} ⇒ {candidate.conclusions}"
                    )
                else:
                    # Incorporate counterexample
                    if verification.counterexample:
                        cex_id = await self.incorporate_counterexample(
                            candidate, verification.counterexample
                        )
                        results["counterexamples"].append(cex_id)
                        results["implications_rejected"].append(
                            {
                                "implication": candidate,
                                "counterexample": verification.counterexample,
                                "reason": verification.reason,
                            }
                        )
                        print(
                            f"❌ Rejected implication: {candidate.premises} ⇒ {candidate.conclusions}"
                        )
                        print(f"   Reason: {verification.reason}")

            # Check convergence
            if self._check_convergence(thresholds):
                print("✅ Convergence reached")
                break

            iteration += 1

        # Finalize results
        results["final_state"] = self.state.to_dict()
        results["exploration_time"] = (datetime.now() - start_time).total_seconds()
        results["merkle_root"] = self.state.J.get_merkle_root()
        results["total_iterations"] = iteration

        return results

    async def _generate_implication(self, index: int) -> Implication:
        """Generate a single implication (stub implementation)."""
        # Simple implication generation based on RegTech domain
        implications_templates = [
            {
                "premises": ["data_class=sensitive"],
                "conclusions": ["must_have_legal_basis"],
                "confidence": 0.9,
                "source": "llm_generation",
                "diversity_key": "sensitive_data_handling",
            },
            {
                "premises": ["api_changed", "breaking_change"],
                "conclusions": ["version_bump_required"],
                "confidence": 0.95,
                "source": "llm_generation",
                "diversity_key": "api_governance",
            },
            {
                "premises": ["has_secrets", "in_production"],
                "conclusions": ["security_risk"],
                "confidence": 0.85,
                "source": "llm_generation",
                "diversity_key": "security_management",
            },
        ]

        template = implications_templates[index % len(implications_templates)]

        return Implication(
            premises=template["premises"],
            conclusions=template["conclusions"],
            confidence=template["confidence"],
            source=template["source"],
            diversity_key=template["diversity_key"],
            costs={
                "time_ms": 100,
                "audit_cost": 10,
                "legal_risk": 0.1,
                "tech_debt": 0.05,
            },
            obligations=["eu_ai_act", "nist_rmf"],
            proofs=["llm_generation", "domain_knowledge"],
        )

    def _check_convergence(self, thresholds: Dict[str, float]) -> bool:
        """Check if exploration has converged."""
        # Simple convergence check
        recent_acceptances = len(
            [
                h
                for h in self.exploration_history[-5:]
                if h.get("type") == "implication_accepted"
            ]
        )

        return recent_acceptances < 1  # Stop if no recent acceptances

    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get statistics about the exploration."""
        total_implications = len(self.state.A)
        total_counterexamples = len(self.state.E)
        total_constraints = len(self.state.K)

        return {
            "total_implications": total_implications,
            "total_counterexamples": total_counterexamples,
            "total_constraints": total_constraints,
            "merkle_root": self.state.J.get_merkle_root(),
            "journal_entries": len(self.state.J.entries),
            "exploration_history": len(self.exploration_history),
        }

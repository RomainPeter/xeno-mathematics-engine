"""
Main controller for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

from core.state import CognitiveState
from verifier.verifier import Verifier
from strategies.bandit import BanditStrategy
from strategies.diversity import DiversityStrategy


@dataclass
class ControllerConfig:
    """Configuration for the controller."""

    max_iterations: int = 100
    timeout_seconds: int = 300
    exploration_budget: float = 1000.0
    verification_budget: float = 500.0
    diversity_weight: float = 0.5
    bandit_alpha: float = 0.1
    bandit_beta: float = 0.1


class Controller:
    """Main controller for Discovery Engine operations."""

    def __init__(self, config: ControllerConfig = None):
        self.config = config or ControllerConfig()
        self.state = CognitiveState()
        self.verifier = Verifier()
        self.bandit_strategy = BanditStrategy(
            alpha=self.config.bandit_alpha, beta=self.config.bandit_beta
        )
        self.diversity_strategy = DiversityStrategy(
            lambda_param=self.config.diversity_weight
        )
        self.operation_history: List[Dict[str, Any]] = []

    async def run_exploration(
        self,
        initial_hypotheses: List[Dict[str, Any]] = None,
        constraints: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run exploration process."""
        # Initialize state
        if initial_hypotheses:
            self.state.H = initial_hypotheses
        if constraints:
            self.state.K = constraints

        # Run exploration loop
        iteration = 0
        start_time = datetime.now()

        while iteration < self.config.max_iterations:
            # Check timeout
            if (
                datetime.now() - start_time
            ).total_seconds() > self.config.timeout_seconds:
                break

            # Generate candidate implications
            candidates = await self._generate_candidates()

            # Select diverse candidates
            selected = self.diversity_strategy.select_diverse_items(candidates, k=3)

            # Verify selected candidates
            for candidate in selected:
                if self._check_budget():
                    result = await self.verifier.verify_implication(candidate.metadata)
                    await self._process_verification_result(result, candidate)

            iteration += 1

        # Generate final results
        results = self._generate_results()
        return results

    async def _generate_candidates(self) -> List[Dict[str, Any]]:
        """Generate candidate implications."""
        candidates = []

        # Simple candidate generation
        for i in range(5):
            candidate = {
                "id": f"candidate_{i}",
                "premises": [f"premise_{i}"],
                "conclusions": [f"conclusion_{i}"],
                "confidence": 0.8,
                "features": [0.1 * i, 0.2 * i, 0.3 * i],
                "metadata": {"generated": True},
            }
            candidates.append(candidate)

        return candidates

    async def _process_verification_result(self, result: Any, candidate: Any):
        """Process verification result."""
        if result.valid:
            # Add to accepted implications
            self.state.A.append(
                {
                    "id": candidate.metadata["id"],
                    "type": "implication",
                    "content": candidate.metadata,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Update bandit strategy
            self.bandit_strategy.update_reward(
                candidate.metadata["id"], reward=1.0, context=None  # Simplified for now
            )
        else:
            # Add to evidence as counterexample
            self.state.E.append(
                {
                    "id": f"cex_{candidate.metadata['id']}",
                    "kind": "counterexample",
                    "content": {
                        "violates": candidate.metadata,
                        "errors": result.errors,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Update bandit strategy
            self.bandit_strategy.update_reward(
                candidate.metadata["id"], reward=0.0, context=None  # Simplified for now
            )

    def _check_budget(self) -> bool:
        """Check if budget constraints are satisfied."""
        # Simplified budget check
        return True

    def _generate_results(self) -> Dict[str, Any]:
        """Generate final results."""
        return {
            "state": self.state.to_dict(),
            "statistics": {
                "hypotheses": len(self.state.H),
                "evidence": len(self.state.E),
                "constraints": len(self.state.K),
                "artifacts": len(self.state.A),
                "journal_entries": len(self.state.J.entries) if self.state.J else 0,
            },
            "bandit_stats": self.bandit_strategy.get_strategy_stats(),
            "diversity_stats": self.diversity_strategy.get_diversity_stats(),
            "verification_stats": self.verifier.get_verification_stats(),
        }

    def get_controller_stats(self) -> Dict[str, Any]:
        """Get controller statistics."""
        return {
            "config": {
                "max_iterations": self.config.max_iterations,
                "timeout_seconds": self.config.timeout_seconds,
                "exploration_budget": self.config.exploration_budget,
                "verification_budget": self.config.verification_budget,
            },
            "state_stats": {
                "hypotheses": len(self.state.H),
                "evidence": len(self.state.E),
                "constraints": len(self.state.K),
                "artifacts": len(self.state.A),
            },
            "operation_history": len(self.operation_history),
        }

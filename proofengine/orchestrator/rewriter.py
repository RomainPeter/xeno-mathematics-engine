"""
Plan rewriter with Φ calculation and cryptographic signatures.
"""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..metrics import WorkUnits
from .strategy_api import Strategy, StrategyContext


@dataclass
class TwoCell:
    """2-category transformation cell with proof guarantees."""

    cell_id: str
    timestamp: str
    strategy_applied: str
    plan_before: Dict[str, Any]
    plan_after: Dict[str, Any]
    phi_before: float
    phi_after: float
    phi_decrease: bool
    signature: Dict[str, str]
    obligations_added: list = None
    delta_v_predicted: float = 0.0
    delta_v_observed: float = 0.0
    selection_result: Dict[str, Any] = None
    work_units: WorkUnits = None

    def __post_init__(self):
        if self.obligations_added is None:
            self.obligations_added = []
        if self.work_units is None:
            self.work_units = WorkUnits()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cell_id": self.cell_id,
            "timestamp": self.timestamp,
            "strategy_applied": self.strategy_applied,
            "plan_before": self.plan_before,
            "plan_after": self.plan_after,
            "phi_before": self.phi_before,
            "phi_after": self.phi_after,
            "phi_decrease": self.phi_decrease,
            "signature": self.signature,
            "obligations_added": self.obligations_added,
            "delta_v_predicted": self.delta_v_predicted,
            "delta_v_observed": self.delta_v_observed,
            "selection_result": self.selection_result,
            "work_units": self.work_units.to_dict(),
        }


class PlanRewriter:
    """Plan rewriter with Φ calculation and cryptographic signatures."""

    def __init__(self, signing_key: str = "local-v0"):
        self.signing_key = signing_key
        self.epsilon = 0.01  # Minimum Φ decrease threshold

    def calculate_phi(self, plan: Dict[str, Any], context: StrategyContext) -> float:
        """Calculate Φ (complexity/risk) of a plan."""
        # Mock Φ calculation - in real implementation, this would be more sophisticated
        # Based on: number of steps, complexity, risk factors, etc.

        steps = plan.get("steps", [])
        phi = len(steps) * 0.1  # Base complexity from step count

        # Add complexity from step types
        for step in steps:
            if step.get("type") == "test":
                phi += 0.05  # Tests add complexity
            elif step.get("type") == "opa":
                phi += 0.03  # OPA rules add complexity
            elif step.get("type") == "docker":
                phi += 0.08  # Docker operations add complexity

        # Add risk factors
        if context.failreason in [
            "policy.secret_egress",
            "policy.dependency_pin_required",
        ]:
            phi += 0.2  # Security-related failures add risk

        return max(0.0, phi)

    def apply_strategy(
        self,
        strategy: Strategy,
        plan: Dict[str, Any],
        context: StrategyContext,
        selection_result: Optional[Dict[str, Any]] = None,
    ) -> TwoCell:
        """Apply a strategy and create a signed TwoCell."""
        import uuid
        from datetime import datetime

        # Calculate Φ before
        phi_before = self.calculate_phi(plan, context)

        # Apply strategy (mock - in real implementation, this would modify the plan)
        plan_after = plan.copy()  # Mock: copy plan
        # In real implementation: plan_after = strategy.apply(plan, context)

        # Calculate Φ after
        phi_after = self.calculate_phi(plan_after, context)

        # Enforce Φ decrease
        phi_decrease = phi_after + self.epsilon < phi_before
        if not phi_decrease:
            raise ValueError(
                f"Φ must strictly decrease: {phi_after:.3f} >= {phi_before:.3f} - {self.epsilon}"
            )

        # Create TwoCell
        cell_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        two_cell = TwoCell(
            cell_id=cell_id,
            timestamp=timestamp,
            strategy_applied=strategy.id,
            plan_before=plan,
            plan_after=plan_after,
            phi_before=phi_before,
            phi_after=phi_after,
            phi_decrease=phi_decrease,
            signature={},  # Will be set below
            obligations_added=strategy.get_obligations_added(context),
            delta_v_predicted=0.0,  # Mock
            delta_v_observed=phi_before - phi_after,  # Actual Φ decrease
            selection_result=selection_result,
            work_units=WorkUnits(
                operators_run=1, proofs_checked=1, tests_run=1, opa_rules_evaluated=1
            ),
        )

        # Sign the TwoCell
        two_cell.signature = self._sign_two_cell(two_cell)

        return two_cell

    def _sign_two_cell(self, two_cell: TwoCell) -> Dict[str, str]:
        """Sign a TwoCell with HMAC-SHA256."""
        # Create canonical JSON representation
        two_cell_dict = two_cell.to_dict()
        # Remove signature field for signing
        two_cell_dict.pop("signature", None)

        canonical_json = json.dumps(two_cell_dict, sort_keys=True, separators=(",", ":"))
        two_cell_bytes = canonical_json.encode("utf-8")

        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.signing_key.encode("utf-8"), two_cell_bytes, hashlib.sha256
        ).digest()

        return {
            "alg": "HMAC-SHA256",
            "key_id": self.signing_key,
            "value": base64.b64encode(signature).decode("utf-8"),
        }

    def verify_two_cell(self, two_cell: TwoCell) -> bool:
        """Verify a TwoCell signature."""
        # Extract signature
        signature = two_cell.signature
        if signature.get("alg") != "HMAC-SHA256":
            return False

        # Recreate canonical JSON
        two_cell_dict = two_cell.to_dict()
        two_cell_dict.pop("signature", None)

        canonical_json = json.dumps(two_cell_dict, sort_keys=True, separators=(",", ":"))
        two_cell_bytes = canonical_json.encode("utf-8")

        # Recreate signature
        expected_signature = hmac.new(
            self.signing_key.encode("utf-8"), two_cell_bytes, hashlib.sha256
        ).digest()

        # Compare
        provided_signature = base64.b64decode(signature["value"])
        return hmac.compare_digest(expected_signature, provided_signature)

    def save_two_cell(self, two_cell: TwoCell, output_path: str) -> None:
        """Save a TwoCell to file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(two_cell.to_dict(), indent=2))

    def load_two_cell(self, input_path: str) -> TwoCell:
        """Load a TwoCell from file."""
        data = json.loads(Path(input_path).read_text())

        return TwoCell(
            cell_id=data["cell_id"],
            timestamp=data["timestamp"],
            strategy_applied=data["strategy_applied"],
            plan_before=data["plan_before"],
            plan_after=data["plan_after"],
            phi_before=data["phi_before"],
            phi_after=data["phi_after"],
            phi_decrease=data["phi_decrease"],
            signature=data["signature"],
            obligations_added=data.get("obligations_added", []),
            delta_v_predicted=data.get("delta_v_predicted", 0.0),
            delta_v_observed=data.get("delta_v_observed", 0.0),
            selection_result=data.get("selection_result"),
            work_units=WorkUnits(**data.get("work_units", {})),
        )

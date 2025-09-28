"""
Main verifier for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .opa_client import OPAClient
from .static_analysis import StaticAnalyzer
from .attestation import AttestationGenerator


@dataclass
class VerificationResult:
    """Result of verification."""

    valid: bool
    errors: List[str]
    warnings: List[str]
    attestation: Optional[Dict[str, Any]] = None
    costs: Dict[str, float] = None
    timestamp: str = ""


class Verifier:
    """Main verifier for Discovery Engine operations."""

    def __init__(self, opa_endpoint: str = "http://localhost:8181/v1/data"):
        self.opa_client = OPAClient(opa_endpoint)
        self.static_analyzer = StaticAnalyzer()
        self.attestation_generator = AttestationGenerator()
        self.verification_history: List[VerificationResult] = []

    async def verify_implication(
        self, implication: Dict[str, Any]
    ) -> VerificationResult:
        """Verify an implication using multiple methods."""
        errors = []
        warnings = []
        costs = {"time_ms": 0, "audit_cost": 0}

        # OPA verification
        try:
            opa_result = await self.opa_client.verify_implication(implication)
            if not opa_result.valid:
                errors.extend(opa_result.errors)
            costs["time_ms"] += opa_result.costs.get("time_ms", 0)
            costs["audit_cost"] += opa_result.costs.get("audit_cost", 0)
        except Exception as e:
            errors.append(f"OPA verification failed: {str(e)}")

        # Static analysis verification
        try:
            static_result = await self.static_analyzer.analyze_implication(implication)
            if not static_result.valid:
                errors.extend(static_result.errors)
            costs["time_ms"] += static_result.costs.get("time_ms", 0)
            costs["audit_cost"] += static_result.costs.get("audit_cost", 0)
        except Exception as e:
            errors.append(f"Static analysis failed: {str(e)}")

        # Generate attestation if valid
        attestation = None
        if not errors:
            try:
                attestation = await self.attestation_generator.generate_attestation(
                    implication, costs
                )
            except Exception as e:
                warnings.append(f"Attestation generation failed: {str(e)}")

        result = VerificationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            attestation=attestation,
            costs=costs,
            timestamp=datetime.now().isoformat(),
        )

        self.verification_history.append(result)
        return result

    async def verify_choreography(
        self, choreography: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a choreography."""
        errors = []
        warnings = []
        costs = {"time_ms": 0, "audit_cost": 0}

        # Verify each operation in the choreography
        operations = choreography.get("operations", [])
        for i, operation in enumerate(operations):
            try:
                op_result = await self.verify_implication(operation)
                if not op_result.valid:
                    errors.append(
                        f"Operation {i} failed: {', '.join(op_result.errors)}"
                    )
                costs["time_ms"] += op_result.costs.get("time_ms", 0)
                costs["audit_cost"] += op_result.costs.get("audit_cost", 0)
            except Exception as e:
                errors.append(f"Operation {i} verification failed: {str(e)}")

        # Generate attestation if valid
        attestation = None
        if not errors:
            try:
                attestation = await self.attestation_generator.generate_attestation(
                    choreography, costs
                )
            except Exception as e:
                warnings.append(f"Attestation generation failed: {str(e)}")

        result = VerificationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            attestation=attestation,
            costs=costs,
            timestamp=datetime.now().isoformat(),
        )

        self.verification_history.append(result)
        return result

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        total_verifications = len(self.verification_history)
        successful_verifications = sum(1 for r in self.verification_history if r.valid)

        return {
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "success_rate": (
                successful_verifications / total_verifications
                if total_verifications > 0
                else 0
            ),
            "total_costs": {
                "time_ms": sum(
                    r.costs.get("time_ms", 0) for r in self.verification_history
                ),
                "audit_cost": sum(
                    r.costs.get("audit_cost", 0) for r in self.verification_history
                ),
            },
        }

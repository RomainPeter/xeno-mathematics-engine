"""
Oracle implementation for Attribute Exploration.
Handles verification of implications using OPA and static analysis.
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OracleResult:
    """Result of oracle verification."""

    valid: bool
    counterexample: Optional[Dict[str, Any]] = None
    attestation: Optional[Dict[str, Any]] = None
    evidence: List[str] = None
    reason: str = ""


class Oracle:
    """Oracle for verifying implications in RegTech/Code domain."""

    def __init__(self, opa_endpoint: str = "http://localhost:8181/v1/data"):
        self.opa_endpoint = opa_endpoint
        self.policies_dir = Path("demo/regtech/policies")
        self.inputs_dir = Path("demo/regtech/inputs")

    async def verify_implication(self, implication: Dict[str, Any]) -> OracleResult:
        """
        Verify an implication using OPA and static analysis.

        Args:
            implication: Dict with 'premises' and 'conclusions'

        Returns:
            OracleResult with verification outcome
        """
        premises = implication.get("premises", [])
        conclusions = implication.get("conclusions", [])

        if not premises or not conclusions:
            return OracleResult(valid=False, reason="Missing premises or conclusions")

        # Try OPA verification first
        opa_result = await self._verify_with_opa(implication)
        if opa_result.valid:
            return opa_result

        # Try static analysis verification
        static_result = await self._verify_with_static_analysis(implication)
        if static_result.valid:
            return static_result

        # If both fail, generate counterexample
        counterexample = await self._generate_counterexample(implication)

        return OracleResult(
            valid=False,
            counterexample=counterexample,
            reason="Implication violated by counterexample",
        )

    async def _verify_with_opa(self, implication: Dict[str, Any]) -> OracleResult:
        """Verify implication using OPA."""
        try:
            # Load relevant policy
            policy_file = self._find_relevant_policy(implication)
            if not policy_file:
                return OracleResult(valid=False, reason="No relevant policy found")

            # Prepare OPA query
            query = {
                "input": {
                    "premises": implication.get("premises", []),
                    "conclusions": implication.get("conclusions", []),
                }
            }

            # Run OPA evaluation (stub implementation)
            result = await self._run_opa_eval(policy_file, query)

            if result.get("result", False):
                return OracleResult(
                    valid=True,
                    attestation={
                        "type": "opa_verification",
                        "policy_file": str(policy_file),
                        "hash": self._hash_file(policy_file),
                    },
                    evidence=["opa_policy_check"],
                )
            else:
                return OracleResult(valid=False, reason="OPA policy violation")

        except Exception as e:
            return OracleResult(
                valid=False, reason=f"OPA verification failed: {str(e)}"
            )

    async def _verify_with_static_analysis(
        self, implication: Dict[str, Any]
    ) -> OracleResult:
        """Verify implication using static analysis."""
        try:
            # Stub implementation for static analysis
            # In practice, this would run actual static analysis tools

            premises = implication.get("premises", [])
            conclusions = implication.get("conclusions", [])

            # Simple heuristic: if premises contain "sensitive" and conclusions contain "legal_basis"
            if any("sensitive" in str(p).lower() for p in premises):
                if any("legal_basis" in str(c).lower() for c in conclusions):
                    return OracleResult(
                        valid=True,
                        attestation={
                            "type": "static_analysis",
                            "tool": "regtech_analyzer",
                            "version": "0.1.0",
                        },
                        evidence=["static_analysis_check"],
                    )

            return OracleResult(valid=False, reason="Static analysis found violations")

        except Exception as e:
            return OracleResult(valid=False, reason=f"Static analysis failed: {str(e)}")

    async def _generate_counterexample(
        self, implication: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate counterexample for failed implication."""
        premises = implication.get("premises", [])
        conclusions = implication.get("conclusions", [])

        # Generate counterexample based on domain knowledge
        counterexample = {
            "id": f"cex_{hash(str(implication)) % 10000}",
            "context": {"domain": "RegTech", "scenario": "sensitive_data_handling"},
            "evidence": [
                "Data classified as sensitive without legal basis",
                "Missing consent mechanism",
                "Inadequate data protection measures",
            ],
            "violates_premise": any("sensitive" in str(p).lower() for p in premises),
            "violates_conclusion": any(
                "legal_basis" in str(c).lower() for c in conclusions
            ),
            "explanation": "Sensitive data found without proper legal basis",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        return counterexample

    def _find_relevant_policy(self, implication: Dict[str, Any]) -> Optional[Path]:
        """Find relevant OPA policy for implication."""
        premises = implication.get("premises", [])

        # Simple policy matching logic
        if any("sensitive" in str(p).lower() for p in premises):
            return self.policies_dir / "retain_sensitive.rego"

        return None

    async def _run_opa_eval(
        self, policy_file: Path, query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run OPA evaluation (stub implementation)."""
        # In practice, this would run: opa eval --data policy_file --input query
        # For now, return a mock result

        await asyncio.sleep(0.1)  # Simulate processing time

        # Mock logic: if query contains sensitive data, require legal basis
        input_data = query.get("input", {})
        premises = input_data.get("premises", [])
        conclusions = input_data.get("conclusions", [])

        has_sensitive = any("sensitive" in str(p).lower() for p in premises)
        has_legal_basis = any("legal_basis" in str(c).lower() for c in conclusions)

        if has_sensitive and has_legal_basis:
            return {"result": True, "evidence": ["legal_basis_provided"]}
        elif has_sensitive and not has_legal_basis:
            return {"result": False, "evidence": ["missing_legal_basis"]}
        else:
            return {"result": True, "evidence": ["no_sensitive_data"]}

    def _hash_file(self, file_path: Path) -> str:
        """Calculate hash of policy file."""
        if file_path.exists():
            import hashlib

            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        return "0" * 64


class MockOracle(Oracle):
    """Mock oracle for testing purposes."""

    def __init__(self):
        super().__init__()
        self.verification_results = {}

    async def verify_implication(self, implication: Dict[str, Any]) -> OracleResult:
        """Mock verification that can be configured for testing."""
        impl_key = str(hash(str(implication)))

        if impl_key in self.verification_results:
            return self.verification_results[impl_key]

        # Default behavior: accept implications with "legal" in conclusions
        conclusions = implication.get("conclusions", [])
        has_legal = any("legal" in str(c).lower() for c in conclusions)

        if has_legal:
            return OracleResult(
                valid=True,
                attestation={"type": "mock_verification"},
                evidence=["mock_legal_check"],
            )
        else:
            counterexample = {
                "id": f"mock_cex_{impl_key}",
                "context": {"domain": "RegTech"},
                "evidence": ["mock_violation"],
                "violates_premise": False,
                "violates_conclusion": True,
                "explanation": "Mock counterexample",
            }

            return OracleResult(
                valid=False,
                counterexample=counterexample,
                reason="Mock verification failed",
            )

    def set_verification_result(
        self, implication: Dict[str, Any], result: OracleResult
    ):
        """Set verification result for specific implication."""
        impl_key = str(hash(str(implication)))
        self.verification_results[impl_key] = result

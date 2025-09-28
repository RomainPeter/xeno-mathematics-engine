"""
Oracle for AE verification using OPA and static analysis.
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any
from datetime import datetime


class Oracle:
    """Oracle for verifying implications using OPA and static analysis."""

    def __init__(self, domain_spec: Dict[str, Any]):
        self.domain_spec = domain_spec
        self.opa_cmd = domain_spec.get("oracle_endpoints", {}).get("opa_cmd", "opa")
        self.rego_pkg = domain_spec.get("oracle_endpoints", {}).get(
            "rego_pkg", "policy"
        )
        self.timeout_ms = domain_spec.get("timeouts", {}).get("verify_ms", 8000)

    def verify_implication(self, implication: Dict[str, Any]) -> Dict[str, Any]:
        """Verify implication using OPA and static analysis."""
        print(f"🔍 Oracle verifying: {implication.get('id', 'unknown')}")

        # Create minimal input for OPA
        input_data = self._create_opa_input(implication)

        # Run OPA evaluation
        opa_result = self._run_opa_evaluation(input_data)

        # Run static analysis if configured
        static_result = self._run_static_analysis(implication)

        # Combine results
        is_valid = opa_result.get("valid", False) and static_result.get("valid", True)

        result = {
            "valid": is_valid,
            "opa_result": opa_result,
            "static_result": static_result,
            "attestation": {
                "type": "oracle_verification",
                "timestamp": datetime.now().isoformat(),
                "hash": self._calculate_attestation_hash(
                    implication, opa_result, static_result
                ),
            },
        }

        if not is_valid:
            result["counterexample"] = self._generate_counterexample(
                implication, opa_result, static_result
            )

        return result

    def _create_opa_input(self, implication: Dict[str, Any]) -> Dict[str, Any]:
        """Create input for OPA evaluation."""
        # Extract premises and conclusions
        premises = implication.get("premises", [])
        # conclusions = implication.get("conclusions", [])  # Not used in this implementation

        # Create minimal input that would trigger the implication
        input_data = {}
        for premise in premises:
            if "data_class" in premise:
                input_data["data_class"] = "sensitive"
            elif "has_legal_basis" in premise:
                input_data["has_legal_basis"] = True
            elif "user_role" in premise:
                input_data["user_role"] = "admin"

        return input_data

    def _run_opa_evaluation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run OPA evaluation."""
        try:
            # Create temporary file for input
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(input_data, f)
                input_file = f.name

            # Run OPA command
            cmd = [self.opa_cmd, "eval", "-i", input_file, f"data.{self.rego_pkg}.deny"]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout_ms / 1000
            )

            # Clean up
            os.unlink(input_file)

            # Parse result
            if result.returncode == 0:
                try:
                    opa_output = json.loads(result.stdout)
                    deny_results = opa_output.get("result", [])
                    is_valid = len(deny_results) == 0
                except json.JSONDecodeError:
                    is_valid = False
                    deny_results = []
            else:
                is_valid = False
                deny_results = [f"OPA error: {result.stderr}"]

            return {
                "valid": is_valid,
                "deny_results": deny_results,
                "opa_stdout": result.stdout,
                "opa_stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "error": "OPA timeout",
                "timeout_ms": self.timeout_ms,
            }
        except Exception as e:
            return {"valid": False, "error": f"OPA execution failed: {str(e)}"}

    def _run_static_analysis(self, implication: Dict[str, Any]) -> Dict[str, Any]:
        """Run static analysis if configured."""
        static_tool = self.domain_spec.get("oracle_endpoints", {}).get(
            "static_analysis"
        )

        if not static_tool:
            return {"valid": True, "tool": "none"}

        try:
            # Mock static analysis
            # In real implementation, would run the configured tool
            return {
                "valid": True,
                "tool": static_tool,
                "issues": [],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "valid": False,
                "tool": static_tool,
                "error": f"Static analysis failed: {str(e)}",
            }

    def _generate_counterexample(
        self,
        implication: Dict[str, Any],
        opa_result: Dict[str, Any],
        static_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate counterexample from failed verification."""
        counterexample = {
            "id": f"cex_{datetime.now().timestamp()}",
            "implication_id": implication.get("id"),
            "type": "verification_failure",
            "opa_deny_results": opa_result.get("deny_results", []),
            "static_issues": static_result.get("issues", []),
            "timestamp": datetime.now().isoformat(),
            "data": {
                "reason": "Implication violated by oracle",
                "opa_details": opa_result.get("opa_stderr", ""),
                "static_details": static_result.get("error", ""),
            },
        }

        return counterexample

    def _calculate_attestation_hash(
        self,
        implication: Dict[str, Any],
        opa_result: Dict[str, Any],
        static_result: Dict[str, Any],
    ) -> str:
        """Calculate attestation hash."""
        import hashlib

        attestation_data = {
            "implication": implication,
            "opa_result": opa_result,
            "static_result": static_result,
            "timestamp": datetime.now().isoformat(),
        }
        return hashlib.sha256(
            json.dumps(attestation_data, sort_keys=True).encode()
        ).hexdigest()[:16]

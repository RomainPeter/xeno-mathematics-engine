"""
Strategy: require_license_allowlist
Ensures license allowlist is configured for dependency management
"""

from typing import Dict, List, Any
from proofengine.core.strategy import Strategy
from proofengine.core.types import Plan, Action, Evidence


class RequireLicenseAllowlistStrategy(Strategy):
    """Strategy to enforce license allowlist configuration"""

    def __init__(self):
        super().__init__(
            name="require_license_allowlist",
            description="Enforce license allowlist for dependencies",
            category="supply-chain",
        )

    def analyze(self, context: Dict[str, Any]) -> List[Evidence]:
        """Analyze for missing license allowlist"""
        evidence = []

        # Check for license allowlist configuration
        if not context.get("license_allowlist"):
            evidence.append(
                Evidence(
                    type="MISSING_LICENSE_ALLOWLIST",
                    severity="high",
                    message="License allowlist not configured",
                    file_path=context.get("config_file", "package.json"),
                    line_number=1,
                )
            )

        # Check for AGPL violations
        dependencies = context.get("dependencies", [])
        for dep in dependencies:
            if dep.get("license") == "AGPL" and "AGPL" not in context.get(
                "license_allowlist", []
            ):
                evidence.append(
                    Evidence(
                        type="AGPL_VIOLATION",
                        severity="critical",
                        message=f"AGPL license detected for {dep['name']} but not in allowlist",
                        file_path=dep.get("file_path", "package.json"),
                        line_number=dep.get("line_number", 1),
                    )
                )

        return evidence

    def plan(self, evidence: List[Evidence]) -> Plan:
        """Plan license allowlist configuration"""
        actions = []

        for ev in evidence:
            if ev.type == "MISSING_LICENSE_ALLOWLIST":
                actions.append(
                    Action(
                        type="CREATE_LICENSE_ALLOWLIST",
                        description="Create license allowlist configuration",
                        file_path="configs/license_allowlist.yaml",
                        content=self._generate_license_allowlist(),
                    )
                )
            elif ev.type == "AGPL_VIOLATION":
                actions.append(
                    Action(
                        type="UPDATE_LICENSE_ALLOWLIST",
                        description="Add AGPL to license allowlist",
                        file_path="configs/license_allowlist.yaml",
                        content=self._add_agpl_to_allowlist(),
                    )
                )

        return Plan(
            strategy=self.name,
            actions=actions,
            expected_outcome="License allowlist configured with proper AGPL handling",
        )

    def _generate_license_allowlist(self) -> str:
        """Generate license allowlist configuration"""
        return """# License Allowlist Configuration
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - ISC
  - GPL-3.0
  - AGPL-3.0

blocked_licenses:
  - GPL-2.0
  - LGPL-2.0

strict_mode: true
require_license_file: true
"""

    def _add_agpl_to_allowlist(self) -> str:
        """Add AGPL to allowlist"""
        return """# License Allowlist Configuration
allowed_licenses:
  - MIT
  - Apache-2.0
  - BSD-3-Clause
  - ISC
  - GPL-3.0
  - AGPL-3.0  # Added for compliance

blocked_licenses:
  - GPL-2.0
  - LGPL-2.0

strict_mode: true
require_license_file: true
"""

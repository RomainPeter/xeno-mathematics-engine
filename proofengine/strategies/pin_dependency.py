"""
Pin dependency strategy for policy.dependency_pin_required failures.

Handles typosquatting and CVE vulnerabilities by pinning dependencies
to specific versions and updating SBOM.
"""

from typing import Any, Dict

from proofengine.orchestrator.strategy_api import (Guards, RewriteOperation,
                                                   RewritePlan, Strategy,
                                                   StrategyContext)


class PinDependencyStrategy(Strategy):
    """Strategy for pinning dependencies to prevent typosquatting and CVE issues."""

    def __init__(self):
        """Initialize the pin dependency strategy."""
        super().__init__(
            id="pin_dependency",
            trigger_codes=["policy.dependency_pin_required"],
            expected_outcomes=["policy_clean", "security_improved"],
        )
        self.guards = Guards(
            max_depth=2,
            max_rewrites_per_fr=1,
            stop_if_plan_grows=True,
            max_plan_size_increase=3,
        )

    def can_apply(self, context: StrategyContext) -> bool:
        """Check if strategy can be applied to context."""
        # Check if this is a dependency-related failure
        if not context.failreason.startswith("policy.dependency"):
            return False

        # Check if plan has dependency information
        plan = context.plan
        if not self._has_dependency_info(plan):
            return False

        # Check depth limit
        if context.depth >= self.guards.max_depth:
            return False

        return True

    def create_rewrite_plan(self, context: StrategyContext) -> RewritePlan:
        """Create rewrite plan for pinning dependencies."""

        # Analyze current dependencies
        dependencies = self._extract_dependencies(context.plan)
        pinned_deps = self._identify_unpinned_dependencies(dependencies)

        if not pinned_deps:
            raise ValueError("No unpinned dependencies found to pin")

        # Create steps for pinning
        steps = []
        for dep_name, dep_info in pinned_deps.items():
            # Step 1: Pin the dependency
            pin_step = {
                "id": f"pin_{dep_name}",
                "operator": "PinDependency",
                "params": {
                    "package": dep_name,
                    "version": dep_info.get("latest_secure", dep_info.get("current", "latest")),
                    "reason": "Security: Prevent typosquatting and CVE vulnerabilities",
                },
            }
            steps.append(pin_step)

            # Step 2: Update SBOM
            sbom_step = {
                "id": f"update_sbom_{dep_name}",
                "operator": "UpdateSBOM",
                "params": {
                    "package": dep_name,
                    "version": dep_info.get("latest_secure", dep_info.get("current", "latest")),
                    "vulnerabilities": dep_info.get("vulnerabilities", []),
                    "license": dep_info.get("license", "unknown"),
                },
            }
            steps.append(sbom_step)

        # Step 3: Rebuild and verify
        rebuild_step = {
            "id": "rebuild_verify",
            "operator": "RebuildVerify",
            "params": {
                "check_vulnerabilities": True,
                "check_licenses": True,
                "timeout_ms": 30000,
            },
        }
        steps.append(rebuild_step)

        return RewritePlan(
            operation=RewriteOperation.INSERT,
            at="before:current_step",
            steps=steps,
            params_patch={
                "security_level": "high",
                "dependency_pinning": "enabled",
                "sbom_updated": True,
            },
        )

    def estimate_success_probability(self, context: StrategyContext) -> float:
        """Estimate success probability for pinning dependencies."""
        base_prob = 0.9  # High success rate for dependency pinning

        # Adjust based on context
        if context.failreason == "policy.dependency_pin_required":
            base_prob += 0.05  # Perfect match

        # Check if plan has clear dependency structure
        if self._has_clear_dependency_structure(context.plan):
            base_prob += 0.03

        # Check for existing security measures
        if self._has_existing_security_measures(context.plan):
            base_prob += 0.02

        return min(base_prob, 1.0)

    def _has_dependency_info(self, plan: Dict[str, Any]) -> bool:
        """Check if plan contains dependency information."""
        steps = plan.get("steps", [])

        # Look for dependency-related steps
        for step in steps:
            if step.get("operator") in [
                "InstallDependency",
                "UpdateDependency",
                "CheckDependency",
            ]:
                return True

        # Check for dependency files in plan metadata
        metadata = plan.get("metadata", {})
        if "dependencies" in metadata or "package_files" in metadata:
            return True

        return False

    def _extract_dependencies(self, plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract dependency information from plan."""
        dependencies = {}

        # Extract from steps
        steps = plan.get("steps", [])
        for step in steps:
            if step.get("operator") in ["InstallDependency", "UpdateDependency"]:
                params = step.get("params", {})
                package = params.get("package")
                if package:
                    dependencies[package] = {
                        "current": params.get("version", "latest"),
                        "operator": step.get("operator"),
                        "vulnerabilities": params.get("vulnerabilities", []),
                        "license": params.get("license", "unknown"),
                    }

        # Extract from metadata
        metadata = plan.get("metadata", {})
        if "dependencies" in metadata:
            for dep_name, dep_info in metadata["dependencies"].items():
                if dep_name not in dependencies:
                    dependencies[dep_name] = dep_info

        return dependencies

    def _identify_unpinned_dependencies(
        self, dependencies: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Identify dependencies that need pinning."""
        unpinned = {}

        for dep_name, dep_info in dependencies.items():
            current_version = dep_info.get("current", "latest")

            # Check if version is pinned (not "latest" or range)
            if (
                current_version in ["latest", "latest-stable", "*"]
                or "~" in current_version
                or "^" in current_version
            ):
                # Find latest secure version
                latest_secure = self._find_latest_secure_version(dep_name, dep_info)
                if latest_secure:
                    unpinned[dep_name] = {
                        **dep_info,
                        "latest_secure": latest_secure,
                        "needs_pinning": True,
                    }

        return unpinned

    def _find_latest_secure_version(self, package: str, dep_info: Dict[str, Any]) -> str:
        """Find latest secure version for package."""
        # Mock implementation - in real scenario, would query package registry
        vulnerabilities = dep_info.get("vulnerabilities", [])

        if not vulnerabilities:
            # No known vulnerabilities, use current or latest
            return dep_info.get("current", "1.0.0")

        # Find version without vulnerabilities
        # This is a simplified mock - real implementation would query security databases
        return "1.0.0"  # Mock secure version

    def _has_clear_dependency_structure(self, plan: Dict[str, Any]) -> bool:
        """Check if plan has clear dependency structure."""
        steps = plan.get("steps", [])
        dependency_steps = [s for s in steps if "dependency" in s.get("operator", "").lower()]
        return len(dependency_steps) > 0

    def _has_existing_security_measures(self, plan: Dict[str, Any]) -> bool:
        """Check if plan already has security measures."""
        steps = plan.get("steps", [])
        security_steps = [
            s
            for s in steps
            if s.get("operator") in ["SecurityScan", "VulnerabilityCheck", "LicenseCheck"]
        ]
        return len(security_steps) > 0

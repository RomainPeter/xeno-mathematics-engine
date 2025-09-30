"""
Strategy: enforce_digest_pin
Ensures all dependencies are pinned to specific digests
"""

from typing import Dict, List, Any
from proofengine.core.strategy import Strategy
from proofengine.core.types import Plan, Action, Evidence


class EnforceDigestPinStrategy(Strategy):
    """Strategy to enforce digest pinning for dependencies"""

    def __init__(self):
        super().__init__(
            name="enforce_digest_pin",
            description="Enforce digest pinning for all dependencies",
            category="supply-chain",
        )

    def analyze(self, context: Dict[str, Any]) -> List[Evidence]:
        """Analyze for unpinned dependencies"""
        evidence = []

        dependencies = context.get("dependencies", [])
        for dep in dependencies:
            # Check for missing digest
            if not dep.get("digest"):
                evidence.append(
                    Evidence(
                        type="MISSING_DIGEST",
                        severity="high",
                        message=f"Dependency {dep['name']} not pinned to digest",
                        file_path=dep.get("file_path", "package.json"),
                        line_number=dep.get("line_number", 1),
                    )
                )

            # Check for floating tags
            version = dep.get("version", "")
            if version in ["latest", "main", "master", "dev"]:
                evidence.append(
                    Evidence(
                        type="FLOATING_TAG",
                        severity="high",
                        message=f"Dependency {dep['name']} uses floating tag '{version}'",
                        file_path=dep.get("file_path", "package.json"),
                        line_number=dep.get("line_number", 1),
                    )
                )

            # Check for invalid digest format
            if dep.get("digest") and not self._is_valid_digest(dep["digest"]):
                evidence.append(
                    Evidence(
                        type="INVALID_DIGEST_FORMAT",
                        severity="medium",
                        message=f"Invalid digest format for {dep['name']}: {dep['digest']}",
                        file_path=dep.get("file_path", "package.json"),
                        line_number=dep.get("line_number", 1),
                    )
                )

        return evidence

    def plan(self, evidence: List[Evidence]) -> Plan:
        """Plan digest pinning actions"""
        actions = []

        for ev in evidence:
            if ev.type == "MISSING_DIGEST":
                actions.append(
                    Action(
                        type="PIN_DIGEST",
                        description="Pin dependency to specific digest",
                        file_path=ev.file_path,
                        content=self._generate_digest_pin(ev.message),
                    )
                )
            elif ev.type == "FLOATING_TAG":
                actions.append(
                    Action(
                        type="REPLACE_FLOATING_TAG",
                        description="Replace floating tag with specific version",
                        file_path=ev.file_path,
                        content=self._replace_floating_tag(ev.message),
                    )
                )
            elif ev.type == "INVALID_DIGEST_FORMAT":
                actions.append(
                    Action(
                        type="FIX_DIGEST_FORMAT",
                        description="Fix digest format",
                        file_path=ev.file_path,
                        content=self._fix_digest_format(ev.message),
                    )
                )

        return Plan(
            strategy=self.name,
            actions=actions,
            expected_outcome="All dependencies pinned to specific digests",
        )

    def _is_valid_digest(self, digest: str) -> bool:
        """Check if digest format is valid"""
        return digest.startswith("sha256:") and len(digest) == 71

    def _generate_digest_pin(self, message: str) -> str:
        """Generate digest pin configuration"""
        return """# Digest pinning configuration
dependencies:
  - name: "dependency-name"
    version: "1.2.3"
    digest: "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    source: "registry.example.com"
"""

    def _replace_floating_tag(self, message: str) -> str:
        """Replace floating tag with specific version"""
        return """# Replace floating tags with specific versions
# Before: "latest", "main", "master"
# After: "1.2.3" with digest pin
"""

    def _fix_digest_format(self, message: str) -> str:
        """Fix digest format"""
        return """# Fix digest format to sha256:hex format
# Format: sha256:64-character-hex-string
"""

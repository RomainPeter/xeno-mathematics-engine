"""
Code compliance candidate proposer.
Implements propose() with LLMAdapter micro-prompt déterministe (seed) -> Candidate.
"""

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .types import Candidate, CodeSnippet


@dataclass
class ProposalContext:
    """Context for candidate proposal."""

    code_snippet: CodeSnippet
    violation_type: str
    rule_id: str
    seed: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MicroPromptTemplate:
    """Template for micro-prompts."""

    def __init__(self, template: str):
        self.template = template

    def render(self, context: ProposalContext) -> str:
        """Render template with context."""
        return self.template.format(
            code=context.code_snippet.content,
            violation_type=context.violation_type,
            rule_id=context.rule_id,
            seed=context.seed,
        )


class DeterministicProposer:
    """Deterministic proposer using seed-based generation."""

    def __init__(self):
        self.templates = {
            "deprecated_api": MicroPromptTemplate(
                "Fix deprecated API usage in: {code}\n"
                "Violation: {violation_type}\n"
                "Rule: {rule_id}\n"
                "Seed: {seed}\n"
                "Provide a compliant replacement."
            ),
            "naming_convention": MicroPromptTemplate(
                "Fix naming convention in: {code}\n"
                "Violation: {violation_type}\n"
                "Rule: {rule_id}\n"
                "Seed: {seed}\n"
                "Use snake_case naming."
            ),
            "security": MicroPromptTemplate(
                "Fix security vulnerability in: {code}\n"
                "Violation: {violation_type}\n"
                "Rule: {rule_id}\n"
                "Seed: {seed}\n"
                "Provide a secure alternative."
            ),
            "code_style": MicroPromptTemplate(
                "Fix code style in: {code}\n"
                "Violation: {violation_type}\n"
                "Rule: {rule_id}\n"
                "Seed: {seed}\n"
                "Follow Python style guidelines."
            ),
        }

    def propose(self, context: ProposalContext) -> Candidate:
        """Generate a candidate solution."""
        # Get template for violation type
        template = self.templates.get(context.violation_type, self.templates["code_style"])

        # Render prompt
        prompt = template.render(context)

        # Generate deterministic response based on seed
        response = self._generate_deterministic_response(prompt, context.seed)

        # Parse response to extract patch, spec, and rationale
        patch, spec, rationale = self._parse_response(response)

        return Candidate(
            patch=patch,
            spec=spec,
            rationale=rationale,
            seed=context.seed,
            metadata={
                "prompt": prompt,
                "violation_type": context.violation_type,
                "rule_id": context.rule_id,
            },
        )

    def _generate_deterministic_response(self, prompt: str, seed: str) -> str:
        """Generate deterministic response based on seed."""
        # Use seed to generate deterministic response
        seed_hash = hashlib.sha256(seed.encode()).hexdigest()

        # Simple deterministic generation based on seed
        if "deprecated_api" in prompt:
            return self._generate_deprecated_api_fix(seed_hash)
        elif "naming_convention" in prompt:
            return self._generate_naming_fix(seed_hash)
        elif "security" in prompt:
            return self._generate_security_fix(seed_hash)
        else:
            return self._generate_generic_fix(seed_hash)

    def _generate_deprecated_api_fix(self, seed_hash: str) -> str:
        """Generate fix for deprecated API."""
        # Use seed to determine fix type
        fix_type = int(seed_hash[:2], 16) % 3

        if fix_type == 0:
            return """PATCH: Replace foo_v1() with foo_v2()
SPEC: Use the new API version
RATIONALE: foo_v1() is deprecated, use foo_v2() for better performance"""
        elif fix_type == 1:
            return """PATCH: Replace deprecated_api_call() with new_api_call()
SPEC: Use the recommended API
RATIONALE: deprecated_api_call() is no longer supported, use new_api_call()"""
        else:
            return """PATCH: Replace old_function() with new_function()
SPEC: Use the updated function
RATIONALE: old_function() is deprecated, new_function() provides the same functionality"""

    def _generate_naming_fix(self, seed_hash: str) -> str:
        """Generate fix for naming convention."""
        # Use seed to determine fix
        fix_type = int(seed_hash[:2], 16) % 2

        if fix_type == 0:
            return """PATCH: Rename camelCaseVariable to snake_case_variable
SPEC: Use snake_case for variable names
RATIONALE: Python convention requires snake_case for variable names"""
        else:
            return """PATCH: Rename PascalCaseFunction to snake_case_function
SPEC: Use snake_case for function names
RATIONALE: Python convention requires snake_case for function names"""

    def _generate_security_fix(self, seed_hash: str) -> str:
        """Generate fix for security vulnerability."""
        # Use seed to determine fix
        fix_type = int(seed_hash[:2], 16) % 2

        if fix_type == 0:
            return """PATCH: Replace eval() with ast.literal_eval()
SPEC: Use safe evaluation method
RATIONALE: eval() is dangerous, use ast.literal_eval() for safe evaluation"""
        else:
            return """PATCH: Replace os.system() with subprocess.run()
SPEC: Use secure subprocess execution
RATIONALE: os.system() is unsafe, use subprocess.run() with proper escaping"""

    def _generate_generic_fix(self, seed_hash: str) -> str:
        """Generate generic fix."""
        return """PATCH: Fix code style issues
SPEC: Follow Python style guidelines
RATIONALE: Code should follow PEP 8 style guidelines"""

    def _parse_response(self, response: str) -> tuple[str, str, str]:
        """Parse response to extract patch, spec, and rationale."""
        lines = response.strip().split("\n")

        patch = ""
        spec = ""
        rationale = ""

        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("PATCH:"):
                current_section = "patch"
                patch = line[6:].strip()
            elif line.startswith("SPEC:"):
                current_section = "spec"
                spec = line[5:].strip()
            elif line.startswith("RATIONALE:"):
                current_section = "rationale"
                rationale = line[10:].strip()
            elif current_section == "patch":
                patch += " " + line
            elif current_section == "spec":
                spec += " " + line
            elif current_section == "rationale":
                rationale += " " + line

        return patch.strip(), spec.strip(), rationale.strip()


class LLMAdapter:
    """Adapter for LLM-based candidate generation."""

    def __init__(self, proposer: Optional[DeterministicProposer] = None):
        self.proposer = proposer or DeterministicProposer()
        self.call_count = 0
        self.total_time = 0.0

    def propose_candidate(self, context: ProposalContext) -> Candidate:
        """Propose a candidate solution."""
        import time

        start_time = time.time()

        try:
            candidate = self.proposer.propose(context)
            self.call_count += 1
            self.total_time += time.time() - start_time
            return candidate
        except Exception as e:
            # Fallback to basic candidate
            return Candidate(
                patch="# Fix implementation needed",
                spec="Fix the violation",
                rationale=f"Error in proposal: {str(e)}",
                seed=context.seed,
                metadata={"error": str(e)},
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get LLM adapter statistics."""
        return {
            "call_count": self.call_count,
            "total_time": self.total_time,
            "average_time": self.total_time / max(self.call_count, 1),
        }

    def reset(self):
        """Reset statistics."""
        self.call_count = 0
        self.total_time = 0.0


class ProposalEngine:
    """Engine for managing candidate proposals."""

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
        self.llm_adapter = llm_adapter or LLMAdapter()
        self.proposal_history: List[Candidate] = []

    def propose(
        self, code_snippet: CodeSnippet, violation_type: str, rule_id: str, seed: str
    ) -> Candidate:
        """Propose a candidate solution."""
        context = ProposalContext(
            code_snippet=code_snippet,
            violation_type=violation_type,
            rule_id=rule_id,
            seed=seed,
            metadata={},
        )

        candidate = self.llm_adapter.propose_candidate(context)
        self.proposal_history.append(candidate)

        return candidate

    def get_proposal_history(self) -> List[Candidate]:
        """Get proposal history."""
        return self.proposal_history.copy()

    def clear_history(self):
        """Clear proposal history."""
        self.proposal_history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_proposals": len(self.proposal_history),
            "llm_statistics": self.llm_adapter.get_statistics(),
        }

"""
Code compliance refiner.
Implements refine() using counterexamples to specialize constraints or edit patches.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from .types import Candidate, Counterexample


@dataclass
class RefinementContext:
    """Context for refinement."""

    original_candidate: Candidate
    counterexamples: List[Counterexample]
    iteration: int
    max_iterations: int = 5
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ConstraintSpecializer:
    """Specializes constraints based on counterexamples."""

    def __init__(self):
        self.constraint_patterns = {
            "deprecated_api": self._specialize_deprecated_api_constraint,
            "naming_convention": self._specialize_naming_constraint,
            "security": self._specialize_security_constraint,
            "code_style": self._specialize_style_constraint,
        }

    def specialize(self, counterexamples: List[Counterexample]) -> Dict[str, Any]:
        """Specialize constraints based on counterexamples."""
        constraints = {}

        for ce in counterexamples:
            rule_id = ce.rule
            if rule_id in self.constraint_patterns:
                rule_constraints = self.constraint_patterns[rule_id](ce)
                constraints[rule_id] = rule_constraints

        return constraints

    def _specialize_deprecated_api_constraint(self, ce: Counterexample) -> Dict[str, Any]:
        """Specialize deprecated API constraint."""
        snippet = ce.snippet.content

        # Extract specific deprecated API from counterexample
        deprecated_apis = []
        for pattern in [
            r"foo_v1",
            r"bar_v1",
            r"baz_v1",
            r"old_function",
            r"legacy_method",
        ]:
            if re.search(pattern, snippet):
                deprecated_apis.append(pattern)

        return {
            "forbidden_apis": deprecated_apis,
            "severity": "high",
            "message": f"Deprecated API usage detected: {', '.join(deprecated_apis)}",
        }

    def _specialize_naming_constraint(self, ce: Counterexample) -> Dict[str, Any]:
        """Specialize naming convention constraint."""
        snippet = ce.snippet.content

        # Extract naming violations
        violations = []
        if re.search(r"def\s+[A-Z]", snippet):
            violations.append("PascalCase function")
        if re.search(r"class\s+[a-z]", snippet):
            violations.append("camelCase class")
        if re.search(r"[a-zA-Z_][a-zA-Z0-9]*[A-Z]", snippet):
            violations.append("camelCase variable")

        return {
            "violations": violations,
            "convention": "snake_case",
            "severity": "medium",
            "message": f"Naming convention violations: {', '.join(violations)}",
        }

    def _specialize_security_constraint(self, ce: Counterexample) -> Dict[str, Any]:
        """Specialize security constraint."""
        snippet = ce.snippet.content

        # Extract security issues
        security_issues = []
        if "eval" in snippet:
            security_issues.append("eval usage")
        if "exec" in snippet:
            security_issues.append("exec usage")
        if "os.system" in snippet:
            security_issues.append("os.system usage")
        if "random.random" in snippet:
            security_issues.append("unsafe random usage")

        return {
            "security_issues": security_issues,
            "severity": "high",
            "message": f"Security issues detected: {', '.join(security_issues)}",
        }

    def _specialize_style_constraint(self, ce: Counterexample) -> Dict[str, Any]:
        """Specialize code style constraint."""
        snippet = ce.snippet.content

        # Extract style issues
        style_issues = []
        if len(snippet) > 120:
            style_issues.append("line too long")
        if snippet.endswith(" "):
            style_issues.append("trailing whitespace")

        return {
            "style_issues": style_issues,
            "severity": "low",
            "message": f"Style issues detected: {', '.join(style_issues)}",
        }


class PatchEditor:
    """Edits patches based on counterexamples."""

    def __init__(self):
        self.edit_strategies = {
            "deprecated_api": self._edit_deprecated_api_patch,
            "naming_convention": self._edit_naming_patch,
            "security": self._edit_security_patch,
            "code_style": self._edit_style_patch,
        }

    def edit_patch(self, candidate: Candidate, counterexamples: List[Counterexample]) -> Candidate:
        """Edit patch based on counterexamples."""
        if not counterexamples:
            return candidate

        # Group counterexamples by rule
        rule_groups = {}
        for ce in counterexamples:
            rule = ce.rule
            if rule not in rule_groups:
                rule_groups[rule] = []
            rule_groups[rule].append(ce)

        # Apply edits for each rule
        edited_patch = candidate.patch
        edited_spec = candidate.spec
        edited_rationale = candidate.rationale

        for rule, ces in rule_groups.items():
            if rule in self.edit_strategies:
                edited_patch, edited_spec, edited_rationale = self.edit_strategies[rule](
                    edited_patch, edited_spec, edited_rationale, ces
                )

        # Create new candidate with edited content
        return Candidate(
            patch=edited_patch,
            spec=edited_spec,
            rationale=edited_rationale,
            seed=candidate.seed,
            metadata={
                **candidate.metadata,
                "refined": True,
                "counterexamples_count": len(counterexamples),
            },
        )

    def _edit_deprecated_api_patch(
        self, patch: str, spec: str, rationale: str, ces: List[Counterexample]
    ) -> tuple[str, str, str]:
        """Edit deprecated API patch."""
        edited_patch = patch

        # Apply specific replacements based on counterexamples
        for ce in ces:
            snippet = ce.snippet.content
            if "foo_v1" in snippet:
                edited_patch = edited_patch.replace("foo_v1", "foo_v2")
            if "bar_v1" in snippet:
                edited_patch = edited_patch.replace("bar_v1", "bar_v2")
            if "baz_v1" in snippet:
                edited_patch = edited_patch.replace("baz_v1", "baz_v2")
            if "old_function" in snippet:
                edited_patch = edited_patch.replace("old_function", "new_function")
            if "legacy_method" in snippet:
                edited_patch = edited_patch.replace("legacy_method", "modern_method")

        edited_spec = f"{spec} (Refined: Updated deprecated APIs)"
        edited_rationale = f"{rationale} (Refined based on {len(ces)} counterexamples)"

        return edited_patch, edited_spec, edited_rationale

    def _edit_naming_patch(
        self, patch: str, spec: str, rationale: str, ces: List[Counterexample]
    ) -> tuple[str, str, str]:
        """Edit naming convention patch."""
        edited_patch = patch

        # Apply naming convention fixes
        for ce in ces:
            # Convert PascalCase to snake_case
            edited_patch = re.sub(r"([A-Z][a-z]+)([A-Z][a-z]+)", r"\1_\2", edited_patch)
            # Convert camelCase to snake_case
            edited_patch = re.sub(r"([a-z])([A-Z])", r"\1_\2", edited_patch)
            edited_patch = edited_patch.lower()

        edited_spec = f"{spec} (Refined: Applied snake_case naming)"
        edited_rationale = f"{rationale} (Refined based on {len(ces)} naming violations)"

        return edited_patch, edited_spec, edited_rationale

    def _edit_security_patch(
        self, patch: str, spec: str, rationale: str, ces: List[Counterexample]
    ) -> tuple[str, str, str]:
        """Edit security patch."""
        edited_patch = patch

        # Apply security fixes
        for ce in ces:
            snippet = ce.snippet.content
            if "eval" in snippet:
                edited_patch = edited_patch.replace("eval(", "ast.literal_eval(")
            if "exec" in snippet:
                edited_patch = edited_patch.replace(
                    "exec(", "# exec(  # SECURITY: Use safer alternative"
                )
            if "os.system" in snippet:
                edited_patch = edited_patch.replace("os.system(", "subprocess.run(")
            if "random.random" in snippet:
                edited_patch = edited_patch.replace("random.random()", "secrets.randbelow(1000)")

        edited_spec = f"{spec} (Refined: Applied security fixes)"
        edited_rationale = f"{rationale} (Refined based on {len(ces)} security issues)"

        return edited_patch, edited_spec, edited_rationale

    def _edit_style_patch(
        self, patch: str, spec: str, rationale: str, ces: List[Counterexample]
    ) -> tuple[str, str, str]:
        """Edit style patch."""
        edited_patch = patch

        # Apply style fixes
        lines = edited_patch.split("\n")
        edited_lines = []

        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Split long lines
            if len(line) > 120:
                # Simple line splitting (in practice, you'd use a proper formatter)
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + " " + word) > 120:
                        edited_lines.append(current_line)
                        current_line = word
                    else:
                        current_line += " " + word if current_line else word
                if current_line:
                    edited_lines.append(current_line)
            else:
                edited_lines.append(line)

        edited_patch = "\n".join(edited_lines)
        edited_spec = f"{spec} (Refined: Applied style fixes)"
        edited_rationale = f"{rationale} (Refined based on {len(ces)} style issues)"

        return edited_patch, edited_spec, edited_rationale


class RefinementEngine:
    """Engine for refining candidates based on counterexamples."""

    def __init__(self):
        self.constraint_specializer = ConstraintSpecializer()
        self.patch_editor = PatchEditor()
        self.refinement_history: List[Dict[str, Any]] = []

    def refine(self, context: RefinementContext) -> Candidate:
        """Refine a candidate based on counterexamples."""
        if not context.counterexamples:
            return context.original_candidate

        # Specialize constraints
        constraints = self.constraint_specializer.specialize(context.counterexamples)

        # Edit patch
        refined_candidate = self.patch_editor.edit_patch(
            context.original_candidate, context.counterexamples
        )

        # Record refinement
        refinement_record = {
            "iteration": context.iteration,
            "original_candidate_id": context.original_candidate.id,
            "refined_candidate_id": refined_candidate.id,
            "counterexamples_count": len(context.counterexamples),
            "constraints": constraints,
            "refinement_type": "patch_edit",
        }

        self.refinement_history.append(refinement_record)

        return refined_candidate

    def get_refinement_history(self) -> List[Dict[str, Any]]:
        """Get refinement history."""
        return self.refinement_history.copy()

    def clear_history(self):
        """Clear refinement history."""
        self.refinement_history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get refinement statistics."""
        if not self.refinement_history:
            return {"total_refinements": 0, "average_counterexamples": 0.0}

        total_refinements = len(self.refinement_history)
        total_counterexamples = sum(
            record["counterexamples_count"] for record in self.refinement_history
        )
        average_counterexamples = total_counterexamples / total_refinements

        return {
            "total_refinements": total_refinements,
            "total_counterexamples": total_counterexamples,
            "average_counterexamples": average_counterexamples,
        }


class AdaptiveRefiner:
    """Adaptive refiner that learns from refinement history."""

    def __init__(self):
        self.refinement_engine = RefinementEngine()
        self.success_patterns: Dict[str, int] = {}
        self.failure_patterns: Dict[str, int] = {}

    def refine(self, context: RefinementContext) -> Candidate:
        """Adaptive refinement based on history."""
        # Analyze counterexamples for patterns
        patterns = self._analyze_counterexample_patterns(context.counterexamples)

        # Update pattern statistics
        for pattern in patterns:
            if context.iteration < 3:  # Assume success for early iterations
                self.success_patterns[pattern] = self.success_patterns.get(pattern, 0) + 1
            else:
                self.failure_patterns[pattern] = self.failure_patterns.get(pattern, 0) + 1

        # Use refinement engine
        refined_candidate = self.refinement_engine.refine(context)

        # Apply adaptive strategies
        if context.iteration > 2:
            refined_candidate = self._apply_adaptive_strategies(refined_candidate, context)

        return refined_candidate

    def _analyze_counterexample_patterns(self, counterexamples: List[Counterexample]) -> List[str]:
        """Analyze patterns in counterexamples."""
        patterns = []

        for ce in counterexamples:
            # Extract patterns from snippet content
            snippet = ce.snippet.content

            if "foo_v1" in snippet:
                patterns.append("deprecated_foo")
            if "bar_v1" in snippet:
                patterns.append("deprecated_bar")
            if "eval" in snippet:
                patterns.append("security_eval")
            if "os.system" in snippet:
                patterns.append("security_os_system")
            if re.search(r"[A-Z][a-z]+[A-Z]", snippet):
                patterns.append("naming_pascal")
            if re.search(r"[a-z][A-Z]", snippet):
                patterns.append("naming_camel")

        return patterns

    def _apply_adaptive_strategies(
        self, candidate: Candidate, context: RefinementContext
    ) -> Candidate:
        """Apply adaptive strategies based on history."""
        # If we've seen this pattern fail before, try a different approach
        patterns = self._analyze_counterexample_patterns(context.counterexamples)

        for pattern in patterns:
            if pattern in self.failure_patterns and self.failure_patterns[pattern] > 2:
                # Try alternative approach
                candidate = self._apply_alternative_strategy(candidate, pattern)

        return candidate

    def _apply_alternative_strategy(self, candidate: Candidate, pattern: str) -> Candidate:
        """Apply alternative strategy for known failure patterns."""
        if pattern == "deprecated_foo":
            # Try different replacement
            candidate.patch = candidate.patch.replace("foo_v2", "modern_foo")
        elif pattern == "security_eval":
            # Try different security approach
            candidate.patch = candidate.patch.replace("ast.literal_eval", "json.loads")
        elif pattern == "naming_pascal":
            # Try different naming approach
            candidate.patch = candidate.patch.replace("snake_case", "kebab-case")

        return candidate

    def get_adaptive_statistics(self) -> Dict[str, Any]:
        """Get adaptive refiner statistics."""
        return {
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "refinement_statistics": self.refinement_engine.get_statistics(),
        }

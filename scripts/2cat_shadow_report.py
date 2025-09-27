"""
2-Category Shadow Report Script.
Executes S1 in shadow mode and produces report with proposals.
"""

import json
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from proofengine.strategies import (
    SpecializeThenRetryStrategy,
    AddMissingTestsStrategy,
    RequireSemverStrategy,
    ChangelogOrBlockStrategy,
    DecomposeMeetStrategy,
    RetryWithHardeningStrategy,
)
from proofengine.orchestrator.strategy_api import StrategyRegistry, StrategyContext
from proofengine.orchestrator.modes import TwoCategoryOrchestrator, ShadowReport
from proofengine.orchestrator.rewriter import PlanRewriter
from proofengine.orchestrator.checker import BasicChecker


class ShadowReportGenerator:
    """Generates shadow reports for 2-category transformations."""

    def __init__(self):
        # Initialize strategy registry
        self.strategy_registry = StrategyRegistry()

        # Register all strategies
        strategies = [
            SpecializeThenRetryStrategy(),
            AddMissingTestsStrategy(),
            RequireSemverStrategy(),
            ChangelogOrBlockStrategy(),
            DecomposeMeetStrategy(),
            RetryWithHardeningStrategy(),
        ]

        for strategy in strategies:
            self.strategy_registry.register(strategy)

        # Initialize orchestrator
        checker = BasicChecker()
        rewriter = PlanRewriter(checker)
        from proofengine.orchestrator.strategy_api import DeterministicSelector

        selector = DeterministicSelector()

        self.orchestrator = TwoCategoryOrchestrator(
            self.strategy_registry, rewriter, selector
        )

    def create_test_contexts(self) -> List[StrategyContext]:
        """Create test contexts for different failreasons."""
        contexts = []

        # Context 1: contract.ambiguous_spec
        contexts.append(
            StrategyContext(
                failreason="contract.ambiguous_spec",
                operator="Generalize",
                plan={
                    "steps": [
                        {
                            "id": "generalize1",
                            "operator": "Generalize",
                            "params": {"hypothesis": "Unclear spec"},
                        }
                    ],
                    "goal": "Test ambiguous specification",
                },
                current_step={
                    "id": "generalize1",
                    "operator": "Generalize",
                    "params": {"hypothesis": "Unclear spec"},
                },
                history=[],
                budgets={"time_ms": 1000, "audit_cost": 10.0},
            )
        )

        # Context 2: coverage.missing_tests
        contexts.append(
            StrategyContext(
                failreason="coverage.missing_tests",
                operator="Verify",
                plan={
                    "steps": [
                        {
                            "id": "verify1",
                            "operator": "Verify",
                            "params": {"target": "test_coverage"},
                        }
                    ],
                    "goal": "Test coverage requirements",
                },
                current_step={
                    "id": "verify1",
                    "operator": "Verify",
                    "params": {"target": "test_coverage"},
                },
                history=[],
                budgets={"time_ms": 2000, "audit_cost": 15.0},
            )
        )

        # Context 3: api.semver_missing
        contexts.append(
            StrategyContext(
                failreason="api.semver_missing",
                operator="Normalize",
                plan={
                    "steps": [
                        {
                            "id": "normalize1",
                            "operator": "Normalize",
                            "params": {"target": "version"},
                        }
                    ],
                    "goal": "Normalize version",
                },
                current_step={
                    "id": "normalize1",
                    "operator": "Normalize",
                    "params": {"target": "version"},
                },
                history=[],
                budgets={"time_ms": 500, "audit_cost": 5.0},
            )
        )

        # Context 4: api.changelog_missing
        contexts.append(
            StrategyContext(
                failreason="api.changelog_missing",
                operator="Normalize",
                plan={
                    "steps": [
                        {
                            "id": "normalize2",
                            "operator": "Normalize",
                            "params": {"target": "changelog"},
                        }
                    ],
                    "goal": "Normalize changelog",
                },
                current_step={
                    "id": "normalize2",
                    "operator": "Normalize",
                    "params": {"target": "changelog"},
                },
                history=[],
                budgets={"time_ms": 800, "audit_cost": 8.0},
            )
        )

        # Context 5: runner.test_failure with complex hypothesis
        contexts.append(
            StrategyContext(
                failreason="runner.test_failure",
                operator="Meet",
                plan={
                    "steps": [
                        {
                            "id": "meet1",
                            "operator": "Meet",
                            "params": {"hypothesis": "A ∧ B"},
                        }
                    ],
                    "goal": "Test complex hypothesis",
                },
                current_step={
                    "id": "meet1",
                    "operator": "Meet",
                    "params": {"hypothesis": "A ∧ B"},
                },
                history=[],
                budgets={"time_ms": 1500, "audit_cost": 12.0},
            )
        )

        # Context 6: nondet.flaky_test
        contexts.append(
            StrategyContext(
                failreason="nondet.flaky_test",
                operator="Meet",
                plan={
                    "steps": [
                        {
                            "id": "meet2",
                            "operator": "Meet",
                            "params": {"hypothesis": "Flaky test"},
                        }
                    ],
                    "goal": "Test flaky behavior",
                },
                current_step={
                    "id": "meet2",
                    "operator": "Meet",
                    "params": {"hypothesis": "Flaky test"},
                },
                history=[],
                budgets={"time_ms": 3000, "audit_cost": 20.0},
            )
        )

        return contexts

    def generate_shadow_report(self) -> ShadowReport:
        """Generate shadow report for all test contexts."""
        contexts = self.create_test_contexts()
        all_proposals = []
        total_strategies = 0
        applicable_strategies = 0

        for context in contexts:
            # Get shadow report for this context
            report = self.orchestrator.execute_shadow_mode(context)
            all_proposals.extend(report.proposals)
            total_strategies += report.total_strategies_evaluated
            applicable_strategies += report.applicable_strategies

        # Calculate overall success rate
        success_rate = (
            applicable_strategies / total_strategies if total_strategies > 0 else 0.0
        )

        return ShadowReport(
            mode="shadow",
            timestamp=datetime.now().isoformat(),
            proposals=all_proposals,
            total_strategies_evaluated=total_strategies,
            applicable_strategies=applicable_strategies,
            success_rate=success_rate,
        )

    def save_artifacts(self, report: ShadowReport, output_dir: str) -> None:
        """Save shadow report and artifacts."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save shadow report
        report_file = output_path / "shadow_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mode": report.mode,
                    "timestamp": report.timestamp,
                    "proposals": report.proposals,
                    "total_strategies_evaluated": report.total_strategies_evaluated,
                    "applicable_strategies": report.applicable_strategies,
                    "success_rate": report.success_rate,
                },
                f,
                indent=2,
            )

        # Save two_cells (empty for shadow mode)
        two_cells_file = output_path / "2cells.jsonl"
        with open(two_cells_file, "w", encoding="utf-8") as f:
            # In shadow mode, we don't actually create two_cells
            pass

        print(f"Shadow report saved to: {report_file}")
        print(f"Two cells file created: {two_cells_file}")

    def print_summary(self, report: ShadowReport) -> None:
        """Print summary of shadow report."""
        print("2-Category Shadow Report Summary")
        print("=" * 50)
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Strategies Evaluated: {report.total_strategies_evaluated}")
        print(f"Applicable Strategies: {report.applicable_strategies}")
        print(f"Success Rate: {report.success_rate:.1%}")
        print(f"Total Proposals: {len(report.proposals)}")

        print("\nProposals by Strategy:")
        strategy_counts = {}
        for proposal in report.proposals:
            strategy_id = proposal["strategy_id"]
            strategy_counts[strategy_id] = strategy_counts.get(strategy_id, 0) + 1

        for strategy_id, count in strategy_counts.items():
            print(f"  {strategy_id}: {count} proposals")

        print("\nProposals by FailReason:")
        failreason_counts = {}
        for proposal in report.proposals:
            # Extract failreason from proposal
            failreason = proposal.get("failreason", "unknown")
            failreason_counts[failreason] = failreason_counts.get(failreason, 0) + 1

        for failreason, count in failreason_counts.items():
            print(f"  {failreason}: {count} proposals")


def main():
    """Main function to generate shadow report."""
    generator = ShadowReportGenerator()

    # Generate shadow report
    report = generator.generate_shadow_report()

    # Print summary
    generator.print_summary(report)

    # Save artifacts
    output_dir = project_root / "out" / "shadow_report"
    generator.save_artifacts(report, str(output_dir))

    # Check if we have enough proposals
    min_proposals = 3  # At least 3 proposals for a meaningful report
    if len(report.proposals) < min_proposals:
        print(
            f"\n⚠️  Warning: Only {len(report.proposals)} proposals generated (minimum: {min_proposals})"
        )
        return False

    print(
        f"\n✅ Shadow report generated successfully with {len(report.proposals)} proposals"
    )
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

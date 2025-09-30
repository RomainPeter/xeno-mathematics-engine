#!/usr/bin/env python3
"""
Metrics calculation for δ (delta) by dimensions H/E/K/A/J
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np
from scipy.stats import pearsonr


@dataclass
class DeltaWeights:
    """Weights for delta calculation by dimension"""

    H: float = 0.3  # History/Context
    E: float = 0.3  # Evidence/Proofs
    K: float = 0.2  # Knowledge/Obligations
    A: float = 0.1  # Artifacts
    J: float = 0.1  # Journal/Logs


class DeltaCalculator:
    """Calculate delta (δ) between intention and result"""

    def __init__(self, weights: Optional[DeltaWeights] = None):
        self.weights = weights or DeltaWeights()

    def calculate_h_dimension(self, context: Dict[str, Any]) -> float:
        """Calculate H (History/Context) dimension delta"""
        # Factors: plan complexity, historical success rate, context richness
        plan_complexity = len(context.get("plan", {}).get("steps", []))
        historical_success = context.get("metrics", {}).get("accept_rate", 0.5)
        context_richness = len(context.get("obligations", []))

        # Normalize and weight
        h_score = (
            min(plan_complexity / 10, 1.0) * 0.4
            + historical_success * 0.4
            + min(context_richness / 5, 1.0) * 0.2
        )

        return 1.0 - h_score  # Delta is inverse of quality

    def calculate_e_dimension(self, evidence: Dict[str, Any]) -> float:
        """Calculate E (Evidence/Proofs) dimension delta"""
        # Factors: proof completeness, verification success, evidence quality
        proof_count = len(evidence.get("proofs", []))
        verification_success = evidence.get("verification", {}).get("success_rate", 0.5)
        evidence_quality = evidence.get("quality_score", 0.5)

        e_score = (
            min(proof_count / 5, 1.0) * 0.3
            + verification_success * 0.4
            + evidence_quality * 0.3
        )

        return 1.0 - e_score

    def calculate_k_dimension(self, obligations: List[str]) -> float:
        """Calculate K (Knowledge/Obligations) dimension delta"""
        # Factors: obligation coverage, compliance rate, knowledge completeness
        obligation_count = len(obligations)
        compliance_rate = sum(1 for o in obligations if o.startswith("k-")) / max(
            obligation_count, 1
        )
        knowledge_completeness = min(obligation_count / 10, 1.0)

        k_score = knowledge_completeness * 0.4 + compliance_rate * 0.6

        return 1.0 - k_score

    def calculate_a_dimension(self, artifacts: Dict[str, Any]) -> float:
        """Calculate A (Artifacts) dimension delta"""
        # Factors: artifact completeness, quality, traceability
        artifact_count = len(artifacts.get("files", []))
        quality_score = artifacts.get("quality", 0.5)
        traceability = artifacts.get("traceability", 0.5)

        a_score = (
            min(artifact_count / 5, 1.0) * 0.3
            + quality_score * 0.4
            + traceability * 0.3
        )

        return 1.0 - a_score

    def calculate_j_dimension(self, journal: Dict[str, Any]) -> float:
        """Calculate J (Journal/Logs) dimension delta"""
        # Factors: log completeness, audit trail, journal quality
        log_count = len(journal.get("entries", []))
        audit_trail = journal.get("audit_trail", {}).get("completeness", 0.5)
        journal_quality = journal.get("quality", 0.5)

        j_score = (
            min(log_count / 10, 1.0) * 0.3 + audit_trail * 0.4 + journal_quality * 0.3
        )

        return 1.0 - j_score

    def calculate_delta(self, state: Dict[str, Any]) -> float:
        """Calculate overall delta from state"""
        # Extract dimensions
        h_delta = self.calculate_h_dimension(state.get("context", {}))
        e_delta = self.calculate_e_dimension(state.get("evidence", {}))
        k_delta = self.calculate_k_dimension(state.get("obligations", []))
        a_delta = self.calculate_a_dimension(state.get("artifacts", {}))
        j_delta = self.calculate_j_dimension(state.get("journal", {}))

        # Weighted sum
        total_delta = (
            h_delta * self.weights.H
            + e_delta * self.weights.E
            + k_delta * self.weights.K
            + a_delta * self.weights.A
            + j_delta * self.weights.J
        )

        return total_delta

    def calculate_incident_correlation(
        self, deltas: List[float], incidents: List[int]
    ) -> float:
        """Calculate correlation between delta and incidents"""
        if len(deltas) != len(incidents) or len(deltas) < 2:
            return 0.0

        try:
            correlation, _ = pearsonr(deltas, incidents)
            return abs(correlation)  # Return absolute correlation
        except Exception:
            return 0.0


class MetricsCollector:
    """Collect and analyze metrics across tasks"""

    def __init__(self, output_dir: str = "artifacts/metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delta_calculator = DeltaCalculator()
        self.metrics_data = []

    def collect_task_metrics(
        self, task_id: str, state: Dict[str, Any], execution_time: float, incidents: int
    ) -> Dict[str, Any]:
        """Collect metrics for a single task"""
        delta = self.delta_calculator.calculate_delta(state)

        metrics = {
            "task_id": task_id,
            "timestamp": time.time(),
            "delta": delta,
            "execution_time": execution_time,
            "incidents": incidents,
            "dimensions": {
                "H": self.delta_calculator.calculate_h_dimension(
                    state.get("context", {})
                ),
                "E": self.delta_calculator.calculate_e_dimension(
                    state.get("evidence", {})
                ),
                "K": self.delta_calculator.calculate_k_dimension(
                    state.get("obligations", [])
                ),
                "A": self.delta_calculator.calculate_a_dimension(
                    state.get("artifacts", {})
                ),
                "J": self.delta_calculator.calculate_j_dimension(
                    state.get("journal", {})
                ),
            },
        }

        self.metrics_data.append(metrics)
        return metrics

    def save_metrics(self, filename: str = "metrics.json"):
        """Save collected metrics to file"""
        metrics_file = self.output_dir / filename
        with open(metrics_file, "w") as f:
            json.dump(self.metrics_data, f, indent=2)
        return metrics_file

    def calculate_correlations(self) -> Dict[str, float]:
        """Calculate correlations between delta and incidents"""
        if len(self.metrics_data) < 2:
            return {}

        deltas = [m["delta"] for m in self.metrics_data]
        incidents = [m["incidents"] for m in self.metrics_data]

        correlation = self.delta_calculator.calculate_incident_correlation(
            deltas, incidents
        )

        return {
            "delta_incident_correlation": correlation,
            "task_count": len(self.metrics_data),
            "mean_delta": np.mean(deltas),
            "mean_incidents": np.mean(incidents),
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        correlations = self.calculate_correlations()

        report = {
            "timestamp": time.time(),
            "summary": correlations,
            "tasks": self.metrics_data,
            "weights": {
                "H": self.delta_calculator.weights.H,
                "E": self.delta_calculator.weights.E,
                "K": self.delta_calculator.weights.K,
                "A": self.delta_calculator.weights.A,
                "J": self.delta_calculator.weights.J,
            },
        }

        # Save report
        report_file = self.output_dir / "metrics_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report


def main():
    """CLI entry point for metrics calculation"""
    import argparse

    parser = argparse.ArgumentParser(description="Calculate delta metrics")
    parser.add_argument("--tasks", help="Path to tasks directory", default="corpus/s2")
    parser.add_argument(
        "--output", help="Output directory", default="artifacts/metrics"
    )
    parser.add_argument(
        "--weights", help="Path to weights file", default="weights.json"
    )

    args = parser.parse_args()

    # Load weights if available
    weights = None
    if Path(args.weights).exists():
        with open(args.weights, "r") as f:
            weights_data = json.load(f)
            weights = DeltaWeights(**weights_data)

    # Initialize collector
    collector = MetricsCollector(args.output)
    if weights:
        collector.delta_calculator.weights = weights

    # Process tasks
    tasks_dir = Path(args.tasks)
    for task_file in tasks_dir.glob("*.json"):
        with open(task_file, "r") as f:
            task_data = json.load(f)

        # Mock state for demonstration
        state = {
            "context": {"plan": {"steps": [{"operator": "test"}]}},
            "evidence": {"proofs": [{"type": "unit_test"}]},
            "obligations": task_data.get("obligations", []),
            "artifacts": {"files": ["test.py"]},
            "journal": {"entries": [{"action": "test"}]},
        }

        # Collect metrics
        metrics = collector.collect_task_metrics(
            task_data["id"],
            state,
            execution_time=1.0,
            incidents=1 if task_data.get("expected_fail") else 0,
        )

        print(f"Task {task_data['id']}: δ={metrics['delta']:.3f}")

    # Generate report
    report = collector.generate_report()
    print(f"Correlation: {report['summary']['delta_incident_correlation']:.3f}")

    # Save metrics
    metrics_file = collector.save_metrics()
    print(f"Metrics saved to: {metrics_file}")


if __name__ == "__main__":
    main()

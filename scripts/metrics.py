#!/usr/bin/env python3
"""
Metrics v0 - δ and V calculation
Collects time_ms, audit_cost, security_risk, info_loss, tech_debt
Calculates δ: distance between X_before/X_after
"""

import json
import csv
from datetime import datetime
from typing import Dict, Any


class MetricsCollector:
    def __init__(self):
        self.metrics = []
        self.weights = {
            "dH": 0.2,  # Hypothesis changes
            "dE": 0.2,  # Evidence changes
            "dK": 0.3,  # Constraint violations
            "dA": 0.2,  # Artifact changes
            "dJ": 0.1,  # Journal changes
        }

    def collect_v_metrics(self, pcap: Dict[str, Any]) -> Dict[str, float]:
        """Collect V metrics from PCAP"""
        justification = pcap.get("justification", {})
        return {
            "time_ms": justification.get("time_ms", 0),
            "audit_cost": justification.get("audit_cost", 0.0),
            "security_risk": justification.get("security_risk", 0.0),
            "info_loss": justification.get("info_loss", 0.0),
            "tech_debt": justification.get("tech_debt", 0.0),
        }

    def calculate_delta(
        self, x_before: Dict[str, Any], x_after: Dict[str, Any]
    ) -> float:
        """Calculate δ (delta) between X_before and X_after"""
        delta_components = {}

        # dH: Hypothesis changes
        h_before = set(h["id"] for h in x_before.get("H", []))
        h_after = set(h["id"] for h in x_after.get("H", []))
        delta_components["dH"] = self.jaccard_distance(h_before, h_after)

        # dE: Evidence changes
        e_before = set(e["id"] for e in x_before.get("E", []))
        e_after = set(e["id"] for e in x_after.get("E", []))
        delta_components["dE"] = self.jaccard_distance(e_before, e_after)

        # dK: Constraint violations (simplified)
        k_before = len(x_before.get("K", []))
        k_after = len(x_after.get("K", []))
        delta_components["dK"] = abs(k_after - k_before) / max(k_before, 1)

        # dA: Artifact changes
        a_before = set(a["id"] for a in x_before.get("A", []))
        a_after = set(a["id"] for a in x_after.get("A", []))
        delta_components["dA"] = self.jaccard_distance(a_before, a_after)

        # dJ: Journal changes
        j_before = len(x_before.get("J", {}).get("entries", []))
        j_after = len(x_after.get("J", {}).get("entries", []))
        delta_components["dJ"] = abs(j_after - j_before) / max(j_before, 1)

        # Weighted combination
        delta = sum(
            self.weights[component] * value
            for component, value in delta_components.items()
        )

        return {"delta": delta, "components": delta_components}

    def jaccard_distance(self, set1: set, set2: set) -> float:
        """Calculate Jaccard distance between two sets"""
        if not set1 and not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return 1.0 - (intersection / union) if union > 0 else 0.0

    def add_metric(
        self,
        task_id: str,
        pcap: Dict[str, Any],
        x_before: Dict[str, Any],
        x_after: Dict[str, Any],
    ):
        """Add metric entry"""
        v_metrics = self.collect_v_metrics(pcap)
        delta_info = self.calculate_delta(x_before, x_after)

        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "pcap_id": pcap.get("id"),
            "v_metrics": v_metrics,
            "delta": delta_info["delta"],
            "delta_components": delta_info["components"],
        }

        self.metrics.append(metric)

    def save_csv(self, output_path: str):
        """Save metrics to CSV"""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if not self.metrics:
                return

            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "task_id",
                    "pcap_id",
                    "time_ms",
                    "audit_cost",
                    "security_risk",
                    "info_loss",
                    "tech_debt",
                    "delta",
                    "dH",
                    "dE",
                    "dK",
                    "dA",
                    "dJ",
                ],
            )
            writer.writeheader()

            for metric in self.metrics:
                row = {
                    "timestamp": metric["timestamp"],
                    "task_id": metric["task_id"],
                    "pcap_id": metric["pcap_id"],
                    **metric["v_metrics"],
                    "delta": metric["delta"],
                    **metric["delta_components"],
                }
                writer.writerow(row)

    def save_json(self, output_path: str):
        """Save metrics to JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "version": "0.1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": self.metrics,
                    "summary": self.calculate_summary(),
                },
                f,
                indent=2,
            )

    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not self.metrics:
            return {}

        deltas = [m["delta"] for m in self.metrics]
        time_ms = [m["v_metrics"]["time_ms"] for m in self.metrics]

        return {
            "total_tasks": len(self.metrics),
            "delta_mean": sum(deltas) / len(deltas),
            "delta_max": max(deltas),
            "time_total_ms": sum(time_ms),
            "time_mean_ms": sum(time_ms) / len(time_ms),
        }


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Metrics collector v0.1")
    parser.add_argument("--input", help="Input metrics JSON file")
    parser.add_argument("--output-csv", help="Output CSV file")
    parser.add_argument("--output-json", help="Output JSON file")

    args = parser.parse_args()

    collector = MetricsCollector()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
            collector.metrics = data.get("metrics", [])

    if args.output_csv:
        collector.save_csv(args.output_csv)
        print(f"Metrics saved to {args.output_csv}")

    if args.output_json:
        collector.save_json(args.output_json)
        print(f"Metrics saved to {args.output_json}")


if __name__ == "__main__":
    main()

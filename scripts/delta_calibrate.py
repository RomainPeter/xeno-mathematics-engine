#!/usr/bin/env python3
"""
Delta calibration script for δ v2
Implements bootstrap, Spearman correlation, and grid search for weights
"""

import argparse
import json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split
import itertools
from typing import Dict, Tuple, Any


class DeltaCalibrator:
    """Delta v2 calibration with bootstrap and Spearman correlation"""

    def __init__(self, bootstrap_samples: int = 1000):
        self.bootstrap_samples = bootstrap_samples
        self.features = [
            "delta_struct_code",
            "dK",
            "delta_dep",
            "delta_test",
            "delta_perf",
            "delta_journal",
        ]
        self.weights = {
            "w_struct": 0.2,
            "w_k": 0.25,
            "w_dep": 0.2,
            "w_test": 0.15,
            "w_perf": 0.1,
            "w_j": 0.1,
        }

    def load_data(self, input_file: str) -> pd.DataFrame:
        """Load metrics data from CSV"""
        df = pd.read_csv(input_file)

        # Ensure required columns exist
        required_cols = ["incidents", "audit_time"] + self.features
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        return df

    def calculate_delta_struct_code(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate δ_struct_code using LibCST analysis"""
        # Simplified cyclomatic-like complexity calculation
        # In real implementation, this would use LibCST
        return np.random.normal(0, 0.1, len(df))  # Placeholder

    def calculate_dK(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate dK (weighted K violations)"""
        # Weighted sum of policy violations
        violations = [
            "semver_violations",
            "changelog_violations",
            "secrets_violations",
            "egress_violations",
            "dep_pin_violations",
            "license_violations",
            "sbom_violations",
            "provenance_violations",
        ]

        dK = np.zeros(len(df))
        for violation in violations:
            if violation in df.columns:
                dK += df[violation] * 0.125  # Equal weight for each violation type

        return dK

    def calculate_delta_dep(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate δ_dep (CVE risk and digest pinning)"""
        # CVE risk (normalized 0-1)
        cve_risk = df.get("cve_risk_max", 0) + df.get("cve_risk_mean", 0) * 0.5

        # Missing digest pins
        missing_digest = df.get("missing_digest_count", 0) / df.get("total_deps", 1)

        return cve_risk + missing_digest

    def calculate_delta_test(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate δ_test (test changes and flakiness)"""
        # Test count changes
        test_delta = df.get("test_count_delta", 0) / df.get("baseline_tests", 1)

        # Coverage changes (approximated)
        coverage_delta = df.get("coverage_delta", 0)

        # Flakiness rate
        flakiness = df.get("flakiness_rate", 0)

        return test_delta + coverage_delta + flakiness

    def calculate_delta_perf(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate δ_perf (performance budget violations)"""
        # P95 latency violations
        p95_violations = df.get("p95_violations", 0) / df.get("p95_budget", 1)

        return p95_violations

    def calculate_delta_journal(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate δ_journal (rework and two_cells)"""
        # Rework count
        rework = df.get("rework_count", 0) / df.get("total_changes", 1)

        # Two cells applied
        two_cells = df.get("two_cells_applied", 0) / df.get("total_changes", 1)

        # Journal length (normalized)
        journal_len = df.get("journal_length", 0) / df.get("baseline_journal", 1)

        return rework + two_cells + journal_len

    def calculate_delta_run(
        self, df: pd.DataFrame, weights: Dict[str, float]
    ) -> np.ndarray:
        """Calculate δ_run using weighted combination"""
        delta_struct = self.calculate_delta_struct_code(df)
        dK = self.calculate_dK(df)
        delta_dep = self.calculate_delta_dep(df)
        delta_test = self.calculate_delta_test(df)
        delta_perf = self.calculate_delta_perf(df)
        delta_journal = self.calculate_delta_journal(df)

        delta_run = pd.Series(
            weights["w_struct"] * delta_struct
            + weights["w_k"] * dK
            + weights["w_dep"] * delta_dep
            + weights["w_test"] * delta_test
            + weights["w_perf"] * delta_perf
            + weights["w_j"] * delta_journal
        )

        return delta_run

    def bootstrap_correlation(
        self, df: pd.DataFrame, weights: Dict[str, float]
    ) -> Tuple[float, float, float]:
        """Bootstrap correlation analysis"""
        delta_run = self.calculate_delta_run(df, weights)

        # Bootstrap samples
        pearson_samples = []
        spearman_samples = []

        for _ in range(self.bootstrap_samples):
            # Bootstrap sample
            indices = np.random.choice(len(df), size=len(df), replace=True)
            sample_df = df.iloc[indices]
            sample_delta = delta_run.iloc[indices]

            # Pearson correlation with incidents
            if "incidents" in sample_df.columns:
                pearson_corr, _ = stats.pearsonr(sample_delta, sample_df["incidents"])
                pearson_samples.append(pearson_corr)

            # Spearman correlation with incidents
            if "incidents" in sample_df.columns:
                spearman_corr, _ = stats.spearmanr(sample_delta, sample_df["incidents"])
                spearman_samples.append(spearman_corr)

        # Calculate confidence intervals
        pearson_ci = np.percentile(pearson_samples, [2.5, 97.5])
        _spearman_ci = np.percentile(spearman_samples, [2.5, 97.5])

        # Final correlations
        final_pearson, _ = stats.pearsonr(delta_run, df["incidents"])
        final_spearman, _ = stats.spearmanr(delta_run, df["incidents"])

        return final_pearson, final_spearman, pearson_ci[0]

    def grid_search_weights(self, df: pd.DataFrame) -> Dict[str, float]:
        """Grid search for optimal weights with constraints"""
        # Define search space with constraints (PR F approach)
        weight_ranges = {
            "w_struct": [0.15, 0.2, 0.25, 0.3, 0.35],
            "w_k": [0.15, 0.2, 0.25, 0.3, 0.35],
            "w_dep": [0.1, 0.15, 0.2, 0.25, 0.3],
            "w_test": [0.1, 0.15, 0.2, 0.25],
            "w_perf": [0.05, 0.1, 0.15, 0.2],
            "w_j": [0.02, 0.05, 0.08, 0.1],
        }

        best_weights = None
        best_correlation = -1

        # Generate all combinations with constraints
        for weights in itertools.product(*weight_ranges.values()):
            weight_dict = dict(zip(weight_ranges.keys(), weights))

            # Apply constraints (PR F approach)
            # Constraint 1: All weights >= 0
            if any(w < 0 for w in weight_dict.values()):
                continue

            # Constraint 2: Sum = 1 (normalize)
            total_weight = sum(weight_dict.values())
            if total_weight <= 0:
                continue
            weight_dict = {k: v / total_weight for k, v in weight_dict.items()}

            # Constraint 3: Minimum correlation threshold
            delta_run = self.calculate_delta_run(df, weight_dict)
            correlation, _ = stats.pearsonr(delta_run, df["incidents"])

            if correlation > best_correlation:
                best_correlation = correlation
                best_weights = weight_dict

        return best_weights or self.weights

    def train_validation_split(
        self, df: pd.DataFrame, test_size: float = 0.3
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Stratified train/validation split"""
        # Stratify by incident category
        stratify_col = (
            "incident_category" if "incident_category" in df.columns else "incidents"
        )

        train_df, val_df = train_test_split(
            df,
            test_size=test_size,
            stratify=df[stratify_col] if stratify_col in df.columns else None,
            random_state=42,
        )

        return train_df, val_df

    def calibrate(
        self, input_file: str, output_file: str, report_file: str
    ) -> Dict[str, Any]:
        """Main calibration process"""
        print("Loading data...")
        df = self.load_data(input_file)

        print("Splitting train/validation...")
        train_df, val_df = self.train_validation_split(df)

        print("Grid searching optimal weights...")
        optimal_weights = self.grid_search_weights(train_df)

        print("Bootstrap correlation analysis...")
        pearson_corr, spearman_corr, pearson_ci_low = self.bootstrap_correlation(
            val_df, optimal_weights
        )

        # Calculate audit_time correlation
        delta_run = self.calculate_delta_run(val_df, optimal_weights)
        audit_corr, _ = stats.pearsonr(delta_run, val_df["audit_time"])

        # Generate report
        report = {
            "calibration_results": {
                "pearson_correlation": float(pearson_corr),
                "spearman_correlation": float(spearman_corr),
                "pearson_ci_low": float(pearson_ci_low),
                "audit_time_correlation": float(audit_corr),
                "meets_gates": {
                    "pearson_ge_06": bool(pearson_corr >= 0.6),
                    "spearman_ge_06": bool(spearman_corr >= 0.6),
                    "pearson_ci_ge_05": bool(pearson_ci_low >= 0.5),
                    "audit_corr_ge_05": bool(audit_corr >= 0.5),
                },
            },
            "optimal_weights": optimal_weights,
            "bootstrap_samples": int(self.bootstrap_samples),
            "validation_size": int(len(val_df)),
            "train_size": int(len(train_df)),
        }

        # Save weights
        with open(output_file, "w") as f:
            json.dump(optimal_weights, f, indent=2)

        # Save report
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print("Calibration complete!")
        print(f"Pearson correlation: {pearson_corr:.3f}")
        print(f"Spearman correlation: {spearman_corr:.3f}")
        print(f"Audit time correlation: {audit_corr:.3f}")
        print(f"Meets gates: {report['calibration_results']['meets_gates']}")

        return report


def main():
    parser = argparse.ArgumentParser(description="Delta v2 calibration")
    parser.add_argument("--input", required=True, help="Input metrics CSV file")
    parser.add_argument("--out", required=True, help="Output weights JSON file")
    parser.add_argument("--report", required=True, help="Output report JSON file")
    parser.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap samples")

    args = parser.parse_args()

    calibrator = DeltaCalibrator(bootstrap_samples=args.bootstrap)
    calibrator.calibrate(args.input, args.out, args.report)


if __name__ == "__main__":
    main()

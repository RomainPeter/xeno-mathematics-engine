"""
Metrics for 2-category transformations with fairness guarantees.
"""

from dataclasses import dataclass
from typing import Dict, Any
import json
import time
from pathlib import Path


@dataclass
class WorkUnits:
    """Work units performed during execution."""

    operators_run: int = 0
    proofs_checked: int = 0
    tests_run: int = 0
    opa_rules_evaluated: int = 0

    def __eq__(self, other) -> bool:
        """Check if work units are identical."""
        if not isinstance(other, WorkUnits):
            return False
        return (
            self.operators_run == other.operators_run
            and self.proofs_checked == other.proofs_checked
            and self.tests_run == other.tests_run
            and self.opa_rules_evaluated == other.opa_rules_evaluated
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operators_run": self.operators_run,
            "proofs_checked": self.proofs_checked,
            "tests_run": self.tests_run,
            "opa_rules_evaluated": self.opa_rules_evaluated,
        }


@dataclass
class TimeBreakdown:
    """Time breakdown by component."""

    t_orchestrator_ms: float = 0.0
    t_llm_ms: float = 0.0
    t_verifier_ms: float = 0.0
    t_io_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "t_orchestrator_ms": self.t_orchestrator_ms,
            "t_llm_ms": self.t_llm_ms,
            "t_verifier_ms": self.t_verifier_ms,
            "t_io_ms": self.t_io_ms,
        }


@dataclass
class CacheInfo:
    """Cache usage information."""

    cache_used: bool = False
    cache_hits: Dict[str, int] = None

    def __post_init__(self):
        if self.cache_hits is None:
            self.cache_hits = {"opa": 0, "sbom": 0, "llm": 0}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"cache_used": self.cache_used, "cache_hits": self.cache_hits}


@dataclass
class ExecutionMetrics:
    """Complete execution metrics with fairness guarantees."""

    work_units: WorkUnits
    time_breakdown: TimeBreakdown
    cache_info: CacheInfo
    steps_count: int = 0
    rewrites_applied: int = 0
    phi_delta: float = 0.0
    mode: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "work_units": self.work_units.to_dict(),
            "time_breakdown": self.time_breakdown.to_dict(),
            "cache_info": self.cache_info.to_dict(),
            "steps_count": self.steps_count,
            "rewrites_applied": self.rewrites_applied,
            "phi_delta": self.phi_delta,
            "mode": self.mode,
            "timestamp": self.timestamp,
        }

    def save_fair_metrics(self, output_path: str, compact: bool = True) -> None:
        """Save metrics in fairness format."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if compact:
            # Compact JSON for performance
            json_str = json.dumps(self.to_dict(), separators=(",", ":"))
        else:
            # Pretty JSON for readability
            json_str = json.dumps(self.to_dict(), indent=2)

        Path(output_path).write_text(json_str)

    @classmethod
    def load_fair_metrics(cls, input_path: str) -> "ExecutionMetrics":
        """Load metrics from fairness format."""
        data = json.loads(Path(input_path).read_text())

        work_units = WorkUnits(**data["work_units"])
        time_breakdown = TimeBreakdown(**data["time_breakdown"])
        cache_info = CacheInfo(**data["cache_info"])

        return cls(
            work_units=work_units,
            time_breakdown=time_breakdown,
            cache_info=cache_info,
            steps_count=data.get("steps_count", 0),
            rewrites_applied=data.get("rewrites_applied", 0),
            phi_delta=data.get("phi_delta", 0.0),
            mode=data.get("mode", ""),
            timestamp=data.get("timestamp", ""),
        )


def compare_metrics_fairness(baseline: ExecutionMetrics, active: ExecutionMetrics) -> bool:
    """Compare metrics for fairness - WorkUnits must be identical."""
    return baseline.work_units == active.work_units


def enforce_fairness_gate(baseline_path: str, active_path: str) -> None:
    """Enforce fairness gate - exit if WorkUnits differ."""
    baseline = ExecutionMetrics.load_fair_metrics(baseline_path)
    active = ExecutionMetrics.load_fair_metrics(active_path)

    if not compare_metrics_fairness(baseline, active):
        print("❌ Fairness gate: different WorkUnits baseline vs active")
        print(f"Baseline: {baseline.work_units.to_dict()}")
        print(f"Active: {active.work_units.to_dict()}")
        exit(1)

    print("✅ Fairness gate: WorkUnits identical")

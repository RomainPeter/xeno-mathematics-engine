from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class RunRecord:
    """Represents a single run's metrics data."""

    run_id: str
    group: str
    weight: float
    metrics: Dict[str, float]
    source_path: str

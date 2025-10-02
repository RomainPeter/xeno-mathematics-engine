from __future__ import annotations

from pathlib import Path
from typing import Any, List

import yaml

from pefc.pipeline.registry import get_step


def load_pipeline(path: Path) -> List[Any]:
    """Load pipeline from YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "steps" not in data:
        raise ValueError("pipeline YAML must contain 'steps' key")

    steps = []
    for step_data in data["steps"]:
        if "type" not in step_data:
            raise ValueError("step must have 'type' key")

        step_type = step_data["type"]
        step_config = step_data.get("config", {})

        step = get_step(step_type, step_config)
        steps.append(step)

    return steps

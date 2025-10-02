from __future__ import annotations

import importlib
from typing import Literal

Backend = Literal["polars", "pandas", "python"]


def choose_backend(prefer: Backend | None = None) -> Backend:
    """
    Choose the best available backend for metrics aggregation.

    Args:
        prefer: Preferred backend if available

    Returns:
        Available backend: polars > pandas > python
    """
    if prefer in ("polars", "pandas", "python"):
        # honour explicit preference if available
        if prefer == "polars" and importlib.util.find_spec("polars"):
            return "polars"
        if prefer == "pandas" and importlib.util.find_spec("pandas"):
            return "pandas"
        if prefer == "python":
            return "python"

    # auto-detect
    if importlib.util.find_spec("polars"):
        return "polars"
    if importlib.util.find_spec("pandas"):
        return "pandas"
    return "python"

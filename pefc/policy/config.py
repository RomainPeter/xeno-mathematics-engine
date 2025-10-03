from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class IDSConfig(BaseModel):
    """Configuration for IDS strategy."""

    name: str = "ucb"
    params: Dict[str, Any] = {}


class RiskConfig(BaseModel):
    """Configuration for risk scorer."""

    name: str = "mean"
    params: Dict[str, Any] = {}


class PolicyConfig(BaseModel):
    """Configuration for policy strategies."""

    ids: IDSConfig = IDSConfig()
    risk: RiskConfig = RiskConfig()

"""
Configuration for Orchestrator.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""

    # Timeouts
    ae_timeout: float = 30.0
    cegis_propose_timeout: float = 10.0
    cegis_verify_timeout: float = 15.0
    cegis_refine_timeout: float = 10.0

    # CEGIS parameters
    cegis_max_iterations: int = 10
    cegis_max_stable_no_improve: int = 3

    # Retry configuration
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    retry_jitter: float = 0.1

    # Determinism
    seed: Optional[int] = None
    hermetic_mode: bool = False

    # Event configuration
    event_retention_days: int = 7
    metrics_collection: bool = True

    # Audit configuration
    audit_dir: str = "audit"
    pcap_retention_days: int = 30
    incident_retention_days: int = 90

    # LLM configuration
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # Verifier configuration
    verifier_timeout: float = 20.0
    verifier_retries: int = 2

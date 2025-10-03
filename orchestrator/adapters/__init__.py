"""
Adapters package.

To avoid heavy deps in lab mode, we expose real adapters lazily and always
expose deterministic stubs (LLMStub, VerifierStub).
"""

from .llm_stub import LLMStub  # lightweight, no external deps
from .verifier_stub import VerifierStub  # lightweight, no external deps

__all__ = [
    "LLMStub",
    "VerifierStub",
]

# Optionally expose real adapters if their dependencies are available
try:
    from .bandit_strategy import BanditConfig, BanditStrategy  # type: ignore
    from .diversity_strategy import DiversityConfig  # type: ignore
    from .diversity_strategy import DiversityStrategy
    from .llm_adapter import LLMAdapter, LLMConfig, LLMResponse  # type: ignore
    from .oracle_adapter import OracleAdapter, OracleConfig  # type: ignore
    from .refinement_strategy import RefinementConfig  # type: ignore
    from .refinement_strategy import RefinementStrategy
    from .synthesis_strategy import SynthesisConfig  # type: ignore
    from .synthesis_strategy import SynthesisStrategy
    from .verifier import VerificationConfig  # type: ignore
    from .verifier import VerificationResult, Verifier

    __all__ += [
        "LLMAdapter",
        "LLMConfig",
        "LLMResponse",
        "Verifier",
        "VerificationResult",
        "VerificationConfig",
        "OracleAdapter",
        "OracleConfig",
        "BanditStrategy",
        "BanditConfig",
        "DiversityStrategy",
        "DiversityConfig",
        "SynthesisStrategy",
        "SynthesisConfig",
        "RefinementStrategy",
        "RefinementConfig",
    ]
except Exception as e:
    # Lab mode can proceed without real adapters
    import logging

    logging.warning(f"Failed to import adapters: {e}")

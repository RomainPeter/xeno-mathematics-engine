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
    from .llm_adapter import LLMAdapter, LLMConfig, LLMResponse  # type: ignore
    from .verifier import Verifier, VerificationResult, VerificationConfig  # type: ignore
    from .oracle_adapter import OracleAdapter, OracleConfig  # type: ignore
    from .bandit_strategy import BanditStrategy, BanditConfig  # type: ignore
    from .diversity_strategy import DiversityStrategy, DiversityConfig  # type: ignore
    from .synthesis_strategy import SynthesisStrategy, SynthesisConfig  # type: ignore
    from .refinement_strategy import RefinementStrategy, RefinementConfig  # type: ignore

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
except Exception:
    # Lab mode can proceed without real adapters
    pass

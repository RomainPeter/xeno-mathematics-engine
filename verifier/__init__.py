"""
Verification components for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from .attestation import AttestationGenerator
from .opa_client import OPAClient
from .static_analysis import StaticAnalyzer
from .verifier import Verifier

__all__ = ["OPAClient", "StaticAnalyzer", "Verifier", "AttestationGenerator"]

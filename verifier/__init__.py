"""
Verification components for Discovery Engine 2-Cat.
Migrated from proof-engine-for-code.
"""

from .opa_client import OPAClient
from .static_analysis import StaticAnalyzer
from .verifier import Verifier
from .attestation import AttestationGenerator

__all__ = ["OPAClient", "StaticAnalyzer", "Verifier", "AttestationGenerator"]

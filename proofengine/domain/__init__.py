"""
Domain-specific modules for code compliance and verification.
Provides types and implementations for code compliance rules.
"""

from .types import Candidate, Verdict, Counterexample, ComplianceRule
from .code_compliance import CodeComplianceEngine, ComplianceChecker
from .rules import DeprecatedAPIRule, NamingConventionRule, SecurityRule

__all__ = [
    "Candidate",
    "Verdict",
    "Counterexample",
    "ComplianceRule",
    "CodeComplianceEngine",
    "ComplianceChecker",
    "DeprecatedAPIRule",
    "NamingConventionRule",
    "SecurityRule",
]

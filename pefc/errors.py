from __future__ import annotations


class PEFCError(Exception):
    """Base exception for all PEFC-related errors."""

    pass


class ConfigError(PEFCError):
    """Configuration-related errors."""

    pass


class MetricsError(PEFCError):
    """Metrics processing and aggregation errors."""

    pass


class ValidationError(PEFCError):
    """Schema validation and contract errors."""

    pass


class PackBuildError(PEFCError):
    """Pack assembly and zip creation errors."""

    pass


class ManifestError(PEFCError):
    """Manifest generation and Merkle computation errors."""

    pass


class SignatureError(PEFCError):
    """Digital signature creation and verification errors."""

    pass


# Exit code mapping for different error types
EXIT_CODE = {
    ValidationError: 20,
    PackBuildError: 30,
    SignatureError: 40,
    ConfigError: 50,
    MetricsError: 60,
    ManifestError: 70,
}

# Special exit codes
SUCCESS_EXIT_CODE = 0
PARTIAL_EXIT_CODE = 10
UNEXPECTED_ERROR_EXIT_CODE = 99

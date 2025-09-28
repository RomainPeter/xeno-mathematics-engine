from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from pefc.errors import SignatureError


@dataclass
class SignConfig:
    """Configuration for digital signature operations."""

    enabled: bool = False
    key_ref: str | None = None
    algorithm: str = "cosign"  # placeholder


def sign_zip(zip_path: Path, cfg: SignConfig) -> Path:
    """
    Sign a zip file with the given configuration.

    Args:
        zip_path: Path to the zip file to sign
        cfg: Signing configuration

    Returns:
        Path to the signature file

    Raises:
        SignatureError: If signing fails or is not configured
    """
    if not cfg.enabled:
        raise SignatureError("Signing is disabled")

    if not cfg.key_ref:
        raise SignatureError("No signing key configured")

    # Create signature file
    sig_path = zip_path.with_suffix(zip_path.suffix + ".sig")

    # Generate a mock signature (real implementation would use actual signing)
    signature_content = f"sig({cfg.algorithm}) for {zip_path.name} with {cfg.key_ref}\n"
    sig_path.write_text(signature_content, encoding="utf-8")

    return sig_path

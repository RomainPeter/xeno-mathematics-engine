from __future__ import annotations
from pathlib import Path
import subprocess
import logging

from pefc.pipeline.core import PackStep, PipelineContext
from pefc.errors import SignatureError

log = logging.getLogger(__name__)


class SignArtifact(PackStep):
    """Sign the zip artifact."""

    def run(self, ctx: PipelineContext) -> None:
        """Sign the zip artifact."""
        if not getattr(ctx.cfg.sign, "enabled", False):
            log.info("sign_artifact: signing disabled")
            return

        log.info("sign_artifact: signing artifact")

        # Find zip file
        zip_files = [arcname for arcname in ctx.files.keys() if arcname.endswith(".zip")]
        if not zip_files:
            raise SignatureError("no zip file found to sign")

        zip_arcname = zip_files[0]
        zip_path = ctx.files[zip_arcname]

        # Get signing method
        method = self.config.get("method", "cosign")
        allow_partial = self.config.get("allow_partial", False)

        try:
            if method == "cosign":
                self._sign_with_cosign(zip_path)
            elif method == "sha256":
                self._sign_with_sha256(zip_path)
            else:
                raise SignatureError(f"unknown signing method: {method}")

            log.info("sign_artifact: successfully signed %s", zip_path)

        except Exception as e:
            if allow_partial:
                ctx.mark_partial(f"signing failed: {e}")
                log.warning("sign_artifact: signing failed but continuing: %s", e)
            else:
                raise SignatureError(f"signing failed: {e}") from e

    def _sign_with_cosign(self, zip_path: Path) -> None:
        """Sign with cosign."""
        try:
            result = subprocess.run(
                ["cosign", "sign-blob", str(zip_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            log.debug("cosign output: %s", result.stdout)
        except subprocess.CalledProcessError as e:
            raise SignatureError(f"cosign failed: {e.stderr}") from e
        except FileNotFoundError:
            raise SignatureError("cosign not found in PATH")

    def _sign_with_sha256(self, zip_path: Path) -> None:
        """Sign with SHA256 (simple hash)."""
        import hashlib

        # Compute SHA256
        h = hashlib.sha256()
        with open(zip_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)

        # Write signature file
        sig_path = zip_path.with_suffix(".zip.sha256")
        sig_path.write_text(f"{h.hexdigest()}  {zip_path.name}\n", encoding="utf-8")

        log.info("sign_artifact: wrote SHA256 signature to %s", sig_path)

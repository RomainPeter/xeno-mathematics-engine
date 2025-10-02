from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from pefc.config.loader import expand_globs, get_config
from pefc.errors import (
    EXIT_CODE,
    PARTIAL_EXIT_CODE,
    SUCCESS_EXIT_CODE,
    UNEXPECTED_ERROR_EXIT_CODE,
    ManifestError,
    MetricsError,
    PackBuildError,
    PEFCError,
    SignatureError,
    ValidationError,
)
from pefc.pack.merkle import PackEntry, build_entries, build_manifest, compute_merkle_root
from pefc.pack.sign import sign_zip
from pefc.pack.zipper import ZipAdder
from pefc.summary import build_summary

log = logging.getLogger(__name__)


class BuildStatus:
    """Build status constants."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"


@dataclass
class BuildResult:
    """Result of a pack build operation."""

    status: str
    exit_code: int
    artifacts: Dict[str, str] = field(
        default_factory=dict
    )  # ex: {"zip": "dist/pack.zip", "manifest": "..."}
    reasons: List[str] = field(default_factory=list)  # human messages
    errors: List[str] = field(default_factory=list)  # stackless error summaries


def _compute_exit_code(status: str, ex: Optional[BaseException]) -> int:
    """Compute exit code based on status and exception."""
    if status == BuildStatus.SUCCESS:
        return SUCCESS_EXIT_CODE
    if status == BuildStatus.PARTIAL:
        return PARTIAL_EXIT_CODE
    if ex is None:
        return 30  # generic failure

    for etype, code in EXIT_CODE.items():
        if isinstance(ex, etype):
            return code
    return UNEXPECTED_ERROR_EXIT_CODE


def run_pack_build(
    *,
    config_path: Optional[str] = None,
    allow_partial: bool = True,
    partial_is_success: bool = False,
) -> BuildResult:
    """
    Run a complete pack build process with error handling.

    Args:
        config_path: Path to configuration file
        allow_partial: Allow partial success (some steps may fail)
        partial_is_success: Treat partial success as success (exit code 0)

    Returns:
        BuildResult with status, exit code, and artifacts
    """
    built_zip: Optional[Path] = None

    try:
        # Load configuration
        cfg_path = Path(config_path) if config_path else None
        cfg = get_config(path=cfg_path, cache=False if cfg_path else True)
        out_dir = Path(cfg.pack.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        last_error: Optional[BaseException] = None
        reasons: List[str] = []
        errors: List[str] = []

        # Initialize variables that might be used later
        summary_path: Optional[Path] = None
        payload: List[tuple[Path, str]] = []
        entries: List[PackEntry] = []
        merkle_root: str = ""
        manifest_json_path: Optional[Path] = None

        # 1) SUMMARY (T01+T04) — peut lever MetricsError/ValidationError
        try:
            metric_sources = expand_globs(cfg.metrics.sources, cfg._base_dir)
            if not metric_sources:
                raise MetricsError("No metrics sources resolved from configuration")

            summary_path = out_dir / "summary.json"
            # Determine backend preference
            prefer_backend = None if cfg.metrics.backend == "auto" else cfg.metrics.backend

            build_summary(
                sources=[Path(p) for p in metric_sources],
                out_path=summary_path,
                include_aggregates=cfg.metrics.include_aggregates,
                weight_key=cfg.metrics.weight_key,
                dedup=cfg.metrics.dedup,
                version=cfg.pack.version,
                prefer_backend=prefer_backend,
                bounded_metrics=cfg.metrics.bounded_metrics,
                schema_path=Path(cfg.metrics.schema_path),
            )
            log.info("build: summary.json generated")
        except (MetricsError, ValidationError) as e:
            log.error(
                "summary: failed",
                extra={"error": type(e).__name__, "error_message": str(e)},
            )
            raise

        # 2) COLLECT PAYLOAD + MANIFEST (T03)
        try:
            if summary_path and summary_path.exists():
                payload.append((summary_path, "metrics/summary.json"))

            # Add other payload files if they exist
            # TODO: Add onepager, sbom, etc. from config

            # Build entries and compute Merkle root
            entries = build_entries(payload)
            merkle_root = compute_merkle_root(entries)
            manifest = build_manifest(entries, merkle_root, cfg.pack.version)

            # Write manifest and merkle files
            manifest_json_path = out_dir / "manifest.json"
            manifest_json_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (out_dir / "merkle.txt").write_text(merkle_root + "\n", encoding="utf-8")

            log.info(
                "build: manifest and merkle computed",
                extra={"merkle_root": merkle_root},
            )
        except (ManifestError, PackBuildError) as e:
            last_error = e
            errors.append(str(e))
            reasons.append("Manifest generation failed")
            if not allow_partial:
                log.error(
                    "manifest: failed",
                    extra={"error": type(e).__name__, "error_message": str(e)},
                )
                raise
            log.warning("manifest: failed, continuing with partial result")

        # 3) ZIP (T02)
        try:
            zip_name = cfg.pack.zip_name.format(
                pack_name=cfg.pack.pack_name, version=cfg.pack.version
            )
            built_zip = out_dir / zip_name
            adder = ZipAdder()

            with ZipFile(built_zip, "w", compression=ZIP_DEFLATED) as z:
                # Add manifest and merkle files
                if manifest_json_path and manifest_json_path.exists():
                    adder.add_text(
                        z,
                        "manifest.json",
                        manifest_json_path.read_text(encoding="utf-8"),
                    )
                if merkle_root:
                    adder.add_text(z, "merkle.txt", merkle_root + "\n")

                # Add payload files
                for src, arc in payload:
                    if src.exists():
                        adder.add_file(z, src, arc)

            log.info("build: zip created", extra={"zip": str(built_zip)})
        except PackBuildError as e:
            last_error = e
            errors.append(str(e))
            reasons.append("Zip creation failed")
            if not allow_partial:
                log.error(
                    "zip: failed",
                    extra={"error": type(e).__name__, "error_message": str(e)},
                )
                raise
            log.warning("zip: failed, continuing with partial result")

        # 4) SIGNATURE (optionnelle)
        if hasattr(cfg, "sign") and cfg.sign.enabled:
            try:
                sig_path = sign_zip(built_zip, cfg.sign)
                log.info("sign: success", extra={"sig": str(sig_path)})
            except SignatureError as e:
                last_error = e
                errors.append(str(e))
                reasons.append("Signature step failed")
                if not allow_partial:
                    log.error(
                        "sign: failed",
                        extra={"error": type(e).__name__, "error_message": str(e)},
                    )
                    raise
                log.warning("sign: failed, continuing with partial result")
        else:
            log.info("sign: skipped")

        # Determine final status
        if last_error is None:
            status = BuildStatus.SUCCESS
        else:
            status = BuildStatus.PARTIAL

        # Compute exit code
        if status == BuildStatus.SUCCESS or (status == BuildStatus.PARTIAL and partial_is_success):
            final_status = BuildStatus.SUCCESS
            exit_code = SUCCESS_EXIT_CODE
        else:
            final_status = status
            exit_code = _compute_exit_code(final_status, last_error)

        log.info(
            f"build: final status={final_status}, exit_code={exit_code}, last_error={last_error}, reasons={reasons}"
        )

        return BuildResult(
            status=final_status,
            exit_code=exit_code,
            artifacts={"zip": str(built_zip)} if built_zip else {},
            reasons=reasons,
            errors=errors,
        )

    except PEFCError as e:
        log.error("build: failed", extra={"error": type(e).__name__, "error_message": str(e)})
        code = _compute_exit_code(BuildStatus.FAILURE, e)
        return BuildResult(
            status=BuildStatus.FAILURE,
            exit_code=code,
            artifacts={"zip": str(built_zip)} if built_zip else {},
            errors=[f"{type(e).__name__}: {e}"],
        )
    except Exception as e:
        log.exception("build: unexpected failure")
        return BuildResult(
            status=BuildStatus.FAILURE,
            exit_code=UNEXPECTED_ERROR_EXIT_CODE,
            artifacts={"zip": str(built_zip)} if built_zip else {},
            errors=[f"UnexpectedError: {e}"],
        )

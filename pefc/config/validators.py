from __future__ import annotations
from pathlib import Path
from typing import List
from .model import RootConfig


def validate_paths(cfg: RootConfig) -> List[str]:
    """Validate file paths in configuration."""
    errors = []

    # Check schema path if validation is enabled
    if cfg.metrics.schema_path and not Path(cfg.metrics.schema_path).exists():
        errors.append(f"Schema path does not exist: {cfg.metrics.schema_path}")

    # Check template path if provided
    if cfg.docs.onepager.template_path and not Path(cfg.docs.onepager.template_path).exists():
        errors.append(f"Template path does not exist: {cfg.docs.onepager.template_path}")

    # Warn about missing SBOM path
    if cfg.sbom.path and not Path(cfg.sbom.path).exists():
        errors.append(f"SBOM path does not exist: {cfg.sbom.path}")

    return errors


def validate_pipelines(cfg: RootConfig) -> List[str]:
    """Validate pipeline configurations."""
    errors = []

    # Known step types
    known_types = {
        "collect",
        "compute_merkle",
        "render_docs",
        "pack_zip",
        "sign",
        "capability",
    }

    for pipeline_name, pipeline_def in cfg.pipelines.defs.items():
        for step in pipeline_def.steps:
            if step.type not in known_types:
                errors.append(f"Unknown step type '{step.type}' in pipeline '{pipeline_name}'")

            # Validate capability steps
            if step.type == "capability":
                if "capabilities" not in step.params:
                    errors.append(
                        f"Capability step in pipeline '{pipeline_name}' missing 'capabilities' parameter"
                    )
                else:
                    capability_ids = step.params.get("capabilities", [])
                    if not isinstance(capability_ids, list):
                        errors.append(
                            f"Capability step 'capabilities' must be a list in pipeline '{pipeline_name}'"
                        )
                    else:
                        # Check if referenced capabilities exist
                        available_ids = {item.id for item in cfg.capabilities.registry}
                        for cap_id in capability_ids:
                            if cap_id not in available_ids:
                                errors.append(
                                    f"Referenced capability '{cap_id}' not found in registry (pipeline '{pipeline_name}')"
                                )

    return errors


def validate_capabilities(cfg: RootConfig) -> List[str]:
    """Validate capabilities configuration."""
    errors = []

    # Check for unique IDs
    ids = [item.id for item in cfg.capabilities.registry]
    if len(ids) != len(set(ids)):
        errors.append("Capability IDs must be unique")

    # Check allowlist/denylist coherence
    if cfg.capabilities.allowlist and cfg.capabilities.denylist:
        overlap = set(cfg.capabilities.allowlist) & set(cfg.capabilities.denylist)
        if overlap:
            errors.append(f"Capabilities cannot be in both allowlist and denylist: {overlap}")

    # Validate module imports (basic check)
    for item in cfg.capabilities.registry:
        if not item.module or ":" not in item.module:
            errors.append(f"Invalid module specification for capability '{item.id}': {item.module}")

    return errors


def validate_metrics(cfg: RootConfig) -> List[str]:
    """Validate metrics configuration."""
    errors = []

    # Validate weight_key
    if not cfg.metrics.weight_key:
        errors.append("Metrics weight_key cannot be empty")

    # Validate backend
    valid_backends = {"auto", "polars", "pandas", "python"}
    if cfg.metrics.backend not in valid_backends:
        errors.append(
            f"Invalid metrics backend '{cfg.metrics.backend}'. Must be one of: {valid_backends}"
        )

    # Validate dedup
    valid_dedup = {"first", "last"}
    if cfg.metrics.dedup not in valid_dedup:
        errors.append(
            f"Invalid dedup strategy '{cfg.metrics.dedup}'. Must be one of: {valid_dedup}"
        )

    return errors


def validate_config(cfg: RootConfig) -> List[str]:
    """Run all validations and return list of errors."""
    errors = []
    errors.extend(validate_paths(cfg))
    errors.extend(validate_pipelines(cfg))
    errors.extend(validate_capabilities(cfg))
    errors.extend(validate_metrics(cfg))
    return errors

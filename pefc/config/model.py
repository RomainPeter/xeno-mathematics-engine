from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PackConfig(BaseModel):
    """Configuration for pack generation."""

    version: str = "v0.1.0"
    pack_name: str = "bench_pack"
    out_dir: str = "dist"
    zip_name: str = "{pack_name}-{version}.zip"
    include_manifest: bool = True
    include_merkle: bool = True


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = "INFO"
    json_mode: bool = False
    gha_annotations: bool = True


class MetricsConfig(BaseModel):
    """Configuration for metrics processing."""

    sources: List[str] = Field(default_factory=lambda: ["bench/metrics/**/*.json"])
    include_aggregates: bool = False
    weight_key: str = "n_items"
    dedup: str = "first"
    backend: str = "auto"
    reduce_policy: str = "intersect"
    bounded_metrics: List[str] = Field(default_factory=lambda: ["coverage_gain", "novelty_avg"])
    schema_path: Optional[str] = "schema/summary.schema.json"


class MerkleConfig(BaseModel):
    """Configuration for Merkle tree computation."""

    chunk_size: int = 65536
    algorithm: str = "sha256"


class SignConfig(BaseModel):
    """Configuration for signing."""

    enabled: bool = False
    provider: str = "cosign"
    key_ref: Optional[str] = None
    required: bool = False


class OnePagerConfig(BaseModel):
    """Configuration for one-pager generation."""

    template_path: Optional[str] = None
    output_file: str = "ONEPAGER.md"


class DocsConfig(BaseModel):
    """Configuration for documentation generation."""

    onepager: OnePagerConfig = Field(default_factory=OnePagerConfig)


class SBOMConfig(BaseModel):
    """Configuration for SBOM."""

    path: Optional[str] = None


class CapabilityItem(BaseModel):
    """Configuration for a capability."""

    id: str
    module: str
    enabled: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)


class CapabilitiesConfig(BaseModel):
    """Configuration for capabilities registry."""

    allowlist: List[str] = Field(default_factory=list)
    denylist: List[str] = Field(default_factory=list)
    registry: List[CapabilityItem] = Field(default_factory=list)


class StepDescriptor(BaseModel):
    """Descriptor for a pipeline step."""

    type: str
    name: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class PipelineDescriptor(BaseModel):
    """Descriptor for a pipeline."""

    name: str
    steps: List[StepDescriptor] = Field(default_factory=list)


class PipelinesConfig(BaseModel):
    """Configuration for pipelines."""

    default: str = "bench_pack"
    defs: Dict[str, PipelineDescriptor] = Field(default_factory=dict)


class RootConfig(BaseModel):
    """Root configuration model."""

    model_config = ConfigDict(extra="forbid")

    pack: PackConfig = Field(default_factory=PackConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    merkle: MerkleConfig = Field(default_factory=MerkleConfig)
    sign: SignConfig = Field(default_factory=SignConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    sbom: SBOMConfig = Field(default_factory=SBOMConfig)
    capabilities: CapabilitiesConfig = Field(default_factory=CapabilitiesConfig)
    pipelines: PipelinesConfig = Field(default_factory=PipelinesConfig)
    profiles: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Runtime metadata
    _base_dir: Optional[str] = None
    _active_env: Optional[str] = None

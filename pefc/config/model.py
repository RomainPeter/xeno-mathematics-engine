from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from pefc.policy.config import PolicyConfig


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_mode: bool = False


class JsonProviderConfig(BaseModel):
    paths: List[str] = Field(default_factory=lambda: ["bench/metrics"])


class BenchAPIProviderConfig(BaseModel):
    base_url: str = "https://bench.example.com/api"
    project_id: str = "proj-123"
    token_env: str = "BENCH_API_TOKEN"
    params: dict = Field(default_factory=dict)


class CacheProviderConfig(BaseModel):
    path: str = ".cache/metrics-runs.jsonl"
    mode: Literal["read", "write", "rw"] = "rw"


class CompositeProviderConfig(BaseModel):
    providers: List[dict] = Field(default_factory=list)


class ProviderConfig(BaseModel):
    kind: Literal["json", "bench_api", "cache", "composite"] = "json"
    json: JsonProviderConfig = Field(default_factory=JsonProviderConfig)
    bench_api: BenchAPIProviderConfig = Field(default_factory=BenchAPIProviderConfig)
    cache: CacheProviderConfig = Field(default_factory=CacheProviderConfig)
    composite: CompositeProviderConfig = Field(default_factory=CompositeProviderConfig)


class MetricsConfig(BaseModel):
    sources: List[str] = Field(default_factory=lambda: ["bench/metrics/**/*.json"])
    include_aggregates: bool = False
    weight_key: str = "n_items"
    dedup: Literal["first", "last"] = "first"
    bounded_metrics: List[str] = Field(default_factory=list)
    schema_path: str = "schema/summary.schema.json"
    backend: str = "auto"  # auto, polars, pandas, python
    provider: Optional[ProviderConfig] = None


class MerkleConfig(BaseModel):
    style: str = "v1"
    chunk_size: int = 1048576


class SignConfig(BaseModel):
    """Digital signature configuration."""

    enabled: bool = False
    key_ref: str | None = None
    algorithm: str = "cosign"


class PackConfig(BaseModel):
    version: str = "v0.1.0"
    pack_name: str = "public-bench-pack"
    out_dir: str = "dist"
    zip_name: str = "{pack_name}-{version}.zip"
    include_manifest: bool = True
    include_merkle: bool = True


class OnePagerConfig(BaseModel):
    template_path: Optional[str] = None  # chemin Jinja2 optionnel
    output_file: str = "ONEPAGER.md"  # relatif à pack.out_dir


class DocsConfig(BaseModel):
    onepager: OnePagerConfig = Field(default_factory=OnePagerConfig)


class SBOMConfig(BaseModel):
    path: Optional[str] = (
        None  # si fourni, on le charge; sinon auto-detect dans out_dir
    )


class RootConfig(BaseModel):
    pack: PackConfig = Field(default_factory=PackConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    merkle: MerkleConfig = Field(default_factory=MerkleConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    sign: SignConfig = Field(default_factory=SignConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    sbom: SBOMConfig = Field(default_factory=SBOMConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)

    model_config = {"extra": "forbid"}

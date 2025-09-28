from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_mode: bool = False


class MetricsConfig(BaseModel):
    sources: List[str] = Field(default_factory=lambda: ["bench/metrics/**/*.json"])
    include_aggregates: bool = False
    weight_key: str = "n_items"
    dedup: Literal["first", "last"] = "first"
    bounded_metrics: List[str] = Field(default_factory=list)
    schema_path: str = "schema/summary.schema.json"
    backend: str = "auto"  # auto, polars, pandas, python


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


class RootConfig(BaseModel):
    pack: PackConfig = Field(default_factory=PackConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    merkle: MerkleConfig = Field(default_factory=MerkleConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    sign: SignConfig = Field(default_factory=SignConfig)

    model_config = {"extra": "forbid"}

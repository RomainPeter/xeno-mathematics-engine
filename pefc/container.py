from __future__ import annotations

import glob
from pathlib import Path
from typing import Any, Dict, Optional

from .capabilities.loader import build_capabilities
from .capabilities.registry import IncidentCapabilityRegistry
from .config.model import RootConfig
from .config.validators import validate_config
from .events import get_event_bus
from .logging import get_logger, init_logging
from .metrics.providers import JsonMetricsProvider


class ServiceContainer:
    """Service container for dependency injection."""

    def __init__(self, cfg: RootConfig):
        self.cfg = cfg
        self._bus = None
        self._logger = None
        self._metrics_provider = None
        self._capability_registry = None
        self._pipelines = {}

    def get_event_bus(self):
        """Get singleton event bus."""
        if self._bus is None:
            self._bus = get_event_bus()
        return self._bus

    def get_logger(self):
        """Get configured logger."""
        if self._logger is None:
            # Setup logging from config
            init_logging(
                level=self.cfg.logging.level,
                json_mode=self.cfg.logging.json_mode,
                gha_annotations=self.cfg.logging.gha_annotations,
            )
            self._logger = get_logger("pefc")
        return self._logger

    def get_metrics_provider(self):
        """Get metrics provider from configuration."""
        if self._metrics_provider is None:
            # Expand glob patterns in sources
            expanded_sources = []
            for pattern in self.cfg.metrics.sources:
                expanded_sources.extend(glob.glob(pattern))

            self._metrics_provider = JsonMetricsProvider(paths=[Path(p) for p in expanded_sources])
        return self._metrics_provider

    def get_capability_registry(self):
        """Get capability registry from configuration."""
        if self._capability_registry is None:
            caps_cfg = self.cfg.capabilities.model_dump()
            caps = build_capabilities(caps_cfg)
            self._capability_registry = IncidentCapabilityRegistry()
            for cap in caps:
                self._capability_registry.register(cap)
        return self._capability_registry

    def get_pipeline(self, name: Optional[str] = None):
        """Get pipeline by name."""
        pipeline_name = name or self.cfg.pipelines.default
        if pipeline_name not in self._pipelines:
            if pipeline_name not in self.cfg.pipelines.defs:
                raise ValueError(f"Pipeline '{pipeline_name}' not found in configuration")

            pipeline_def = self.cfg.pipelines.defs[pipeline_name]
            self._pipelines[pipeline_name] = self._build_pipeline(pipeline_def)

        return self._pipelines[pipeline_name]

    def _build_pipeline(self, pipeline_def):
        """Build pipeline from descriptor."""
        from .pipeline.core import Pipeline
        from .pipeline.steps import (CollectSeeds, ComputeMerkle, PackZip,
                                     RenderDocs, RunCapabilities, SignArtifact)

        # Step type mapping
        step_classes = {
            "collect": CollectSeeds,
            "compute_merkle": ComputeMerkle,
            "render_docs": RenderDocs,
            "pack_zip": PackZip,
            "sign": SignArtifact,
            "capability": RunCapabilities,
        }

        steps = []
        for step_desc in pipeline_def.steps:
            if step_desc.type not in step_classes:
                raise ValueError(f"Unknown step type: {step_desc.type}")

            step_class = step_classes[step_desc.type]
            step_name = step_desc.name or step_desc.type
            step_params = step_desc.params.copy()

            # Special handling for capability steps
            if step_desc.type == "capability":
                step_params["registry"] = self.get_capability_registry()

            step = step_class(name=step_name, **step_params)
            steps.append(step)

        return Pipeline(steps)

    def build_context(self) -> Dict[str, Any]:
        """Build initial pipeline context."""
        return {
            "config": self.cfg,
            "bus": self.get_event_bus(),
            "logger": self.get_logger(),
            "metrics_provider": self.get_metrics_provider(),
            "capability_registry": self.get_capability_registry(),
        }

    def validate(self) -> list[str]:
        """Validate configuration and return any errors."""
        return validate_config(self.cfg)

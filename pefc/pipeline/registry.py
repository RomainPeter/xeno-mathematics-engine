from __future__ import annotations

from typing import Any, Dict, Type

from pefc.pipeline.core import PackStep
from pefc.pipeline.steps.build_summary import BuildSummary
from pefc.pipeline.steps.collect_seeds import CollectSeeds
from pefc.pipeline.steps.compute_merkle import ComputeMerkle
from pefc.pipeline.steps.pack_zip import PackZip
from pefc.pipeline.steps.render_docs import RenderDocs
from pefc.pipeline.steps.sign_artifact import SignArtifact

# Registry mapping step types to classes
REGISTRY: Dict[str, Type[PackStep]] = {
    "CollectSeeds": CollectSeeds,
    "BuildSummary": BuildSummary,
    "RenderDocs": RenderDocs,
    "ComputeMerkle": ComputeMerkle,
    "PackZip": PackZip,
    "SignArtifact": SignArtifact,
}


def get_step(step_type: str, config: Dict[str, Any]) -> PackStep:
    """Get step instance by type and config."""
    if step_type not in REGISTRY:
        raise ValueError(f"unknown step type: {step_type}")

    step_class = REGISTRY[step_type]
    return step_class(config)

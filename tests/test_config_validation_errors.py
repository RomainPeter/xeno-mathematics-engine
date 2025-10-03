from __future__ import annotations

import os
import tempfile

from pefc.config.loader import load_config
from pefc.config.validators import validate_config


def test_unknown_step_type():
    """Test validation error for unknown step type."""
    config_data = """
pack:
  version: "v1.0.0"

pipelines:
  defs:
    test_pipeline:
      name: "Test Pipeline"
      steps:
        - type: "unknown_step"
          name: "UnknownStep"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("Unknown step type 'unknown_step'" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_capability_step_missing_capabilities():
    """Test validation error for capability step missing capabilities parameter."""
    config_data = """
pack:
  version: "v1.0.0"

pipelines:
  defs:
    test_pipeline:
      name: "Test Pipeline"
      steps:
        - type: "capability"
          name: "RunCapabilities"
          # Missing params.capabilities
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("missing 'capabilities' parameter" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_capability_step_invalid_capabilities():
    """Test validation error for capability step with invalid capabilities parameter."""
    config_data = """
pack:
  version: "v1.0.0"

capabilities:
  registry:
    - id: "test-cap"
      module: "test.module:TestCap"
      enabled: true

pipelines:
  defs:
    test_pipeline:
      name: "Test Pipeline"
      steps:
        - type: "capability"
          name: "RunCapabilities"
          params:
            capabilities: "not-a-list"  # Should be a list
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("must be a list" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_capability_step_unknown_capability():
    """Test validation error for capability step referencing unknown capability."""
    config_data = """
pack:
  version: "v1.0.0"

capabilities:
  registry:
    - id: "test-cap"
      module: "test.module:TestCap"
      enabled: true

pipelines:
  defs:
    test_pipeline:
      name: "Test Pipeline"
      steps:
        - type: "capability"
          name: "RunCapabilities"
          params:
            capabilities: ["test-cap", "unknown-cap"]  # unknown-cap doesn't exist
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("Referenced capability 'unknown-cap' not found" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_invalid_metrics_backend():
    """Test validation error for invalid metrics backend."""
    config_data = """
pack:
  version: "v1.0.0"

metrics:
  backend: "invalid_backend"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("Invalid metrics backend 'invalid_backend'" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_invalid_dedup_strategy():
    """Test validation error for invalid dedup strategy."""
    config_data = """
pack:
  version: "v1.0.0"

metrics:
  dedup: "invalid_dedup"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("Invalid dedup strategy 'invalid_dedup'" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_empty_weight_key():
    """Test validation error for empty weight key."""
    config_data = """
pack:
  version: "v1.0.0"

metrics:
  weight_key: ""
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("Metrics weight_key cannot be empty" in error for error in errors)

        finally:
            os.unlink(f.name)


def test_capability_allowlist_denylist_overlap():
    """Test validation error for overlapping allowlist and denylist."""
    config_data = """
pack:
  version: "v1.0.0"

capabilities:
  allowlist: ["cap1", "cap2"]
  denylist: ["cap2", "cap3"]  # cap2 is in both
  registry:
    - id: "cap1"
      module: "test.module:Cap1"
      enabled: true
    - id: "cap2"
      module: "test.module:Cap2"
      enabled: true
    - id: "cap3"
      module: "test.module:Cap3"
      enabled: true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            errors = validate_config(cfg)

            assert len(errors) > 0
            assert any("cannot be in both allowlist and denylist" in error for error in errors)
            assert any("cap2" in error for error in errors)

        finally:
            os.unlink(f.name)

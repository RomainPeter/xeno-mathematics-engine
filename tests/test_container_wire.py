from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pefc.config.loader import load_config
from pefc.container import ServiceContainer


def test_container_basic():
    """Test basic container functionality."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)
    container = ServiceContainer(cfg)

    # Test validation
    errors = container.validate()
    assert len(errors) == 0, f"Configuration validation failed: {errors}"

    # Test service building
    bus = container.get_event_bus()
    assert bus is not None

    logger = container.get_logger()
    assert logger is not None

    metrics_provider = container.get_metrics_provider()
    assert metrics_provider is not None

    registry = container.get_capability_registry()
    assert registry is not None


def test_container_capability_registry():
    """Test capability registry construction."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)
    container = ServiceContainer(cfg)

    registry = container.get_capability_registry()
    handlers = registry.list_handlers()

    # Should have the configured capabilities
    handler_ids = [h["id"] for h in handlers]
    assert "hs-tree" in handler_ids
    assert "opa-rego" in handler_ids
    assert "ids-synth" in handler_ids


def test_container_pipeline():
    """Test pipeline construction."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)
    container = ServiceContainer(cfg)

    # Test default pipeline
    pipeline = container.get_pipeline()
    assert pipeline is not None

    # Test named pipeline
    pipeline = container.get_pipeline("bench_pack")
    assert pipeline is not None

    # Test non-existent pipeline
    try:
        container.get_pipeline("non_existent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_container_context():
    """Test context building."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)
    container = ServiceContainer(cfg)

    context = container.build_context()

    assert "config" in context
    assert "bus" in context
    assert "logger" in context
    assert "metrics_provider" in context
    assert "capability_registry" in context

    assert context["config"] == cfg
    assert context["bus"] is not None
    assert context["logger"] is not None
    assert context["metrics_provider"] is not None
    assert context["capability_registry"] is not None


def test_container_with_custom_config():
    """Test container with custom configuration."""
    config_data = """
pack:
  version: "v1.0.0"
  pack_name: "test-pack"

logging:
  level: "DEBUG"
  json_mode: true

capabilities:
  registry:
    - id: "test-cap"
      module: "pefc.capabilities.handlers.hstree:HSTreeHandler"
      enabled: true
      params: {}

pipelines:
  default: "test_pipeline"
  defs:
    test_pipeline:
      name: "Test Pipeline"
      steps:
        - type: "collect"
          name: "CollectSeeds"
        - type: "capability"
          name: "RunTestCap"
          params:
            capabilities: ["test-cap"]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            container = ServiceContainer(cfg)

            # Test validation
            errors = container.validate()
            assert len(errors) == 0, f"Configuration validation failed: {errors}"

            # Test services
            registry = container.get_capability_registry()
            handlers = registry.list_handlers()
            assert len(handlers) == 1
            assert handlers[0]["id"] == "test-cap"

            # Test pipeline
            pipeline = container.get_pipeline()
            assert pipeline is not None

        finally:
            os.unlink(f.name)


def test_container_singleton_services():
    """Test that services are singletons."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)
    container = ServiceContainer(cfg)

    # Multiple calls should return the same instance
    bus1 = container.get_event_bus()
    bus2 = container.get_event_bus()
    assert bus1 is bus2

    logger1 = container.get_logger()
    logger2 = container.get_logger()
    assert logger1 is logger2

    registry1 = container.get_capability_registry()
    registry2 = container.get_capability_registry()
    assert registry1 is registry2


def test_container_with_profile():
    """Test container with environment profile."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path, env="dev")
    container = ServiceContainer(cfg)

    # Should have dev profile settings
    assert cfg.logging.level == "DEBUG"
    assert cfg.logging.json_mode is True
    assert cfg.sign.enabled is False

    # Container should work with profile
    errors = container.validate()
    assert len(errors) == 0, f"Configuration validation failed: {errors}"

    # Services should build successfully
    bus = container.get_event_bus()
    logger = container.get_logger()
    registry = container.get_capability_registry()

    assert bus is not None
    assert logger is not None
    assert registry is not None

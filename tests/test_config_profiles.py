from __future__ import annotations
import os
import tempfile
from pathlib import Path
from pefc.config.loader import load_config


def test_load_config_base():
    """Test loading base configuration."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)

    assert cfg.pack.version == "v0.2.0"
    assert cfg.pack.pack_name == "public-bench"
    assert cfg.logging.level == "INFO"
    assert cfg.logging.json_mode is False
    assert cfg.sign.enabled is False


def test_load_config_with_env():
    """Test loading configuration with environment profile."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path, env="dev")

    # Should have dev profile overrides
    assert cfg.logging.level == "DEBUG"
    assert cfg.logging.json_mode is True
    assert cfg.sign.enabled is False


def test_load_config_hardening():
    """Test loading hardening profile."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path, env="hardening")

    # Should have hardening profile overrides
    assert cfg.logging.level == "INFO"
    assert cfg.logging.json_mode is True
    assert cfg.sign.enabled is True
    assert cfg.sign.required is True


def test_load_config_partner():
    """Test loading partner profile."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path, env="partner")

    # Should have partner profile overrides
    assert "partner/metrics/**/*.json" in cfg.metrics.sources
    assert "hs-tree" in cfg.capabilities.allowlist
    assert "opa-rego" in cfg.capabilities.denylist


def test_config_validation():
    """Test configuration validation."""
    config_path = Path("config/pack.yaml")
    cfg = load_config(config_path)

    # Should be valid
    assert cfg.pack.version is not None
    assert cfg.logging.level is not None
    assert len(cfg.capabilities.registry) > 0
    assert len(cfg.pipelines.defs) > 0


def test_config_with_temp_file():
    """Test loading configuration from temporary file."""
    config_data = """
pack:
  version: "v1.0.0"
  pack_name: "test-pack"

logging:
  level: "DEBUG"
  json: true

profiles:
  test:
    logging:
      level: "ERROR"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            cfg = load_config(f.name)
            assert cfg.pack.version == "v1.0.0"
            assert cfg.pack.pack_name == "test-pack"
            assert cfg.logging.level == "DEBUG"

            # Test with profile
            cfg_with_profile = load_config(f.name, env="test")
            assert cfg_with_profile.logging.level == "ERROR"

        finally:
            os.unlink(f.name)

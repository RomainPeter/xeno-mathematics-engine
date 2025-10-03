from __future__ import annotations

import os
import tempfile

from pefc.config.loader import load_config


def test_env_substitution_basic():
    """Test basic environment variable substitution."""
    config_data = """
pack:
  version: "${PACK_VERSION:-v1.0.0}"
  pack_name: "test-${ENV_NAME:-default}"

logging:
  level: "${LOG_LEVEL:-INFO}"
  json_mode: false
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            # Test with default values
            cfg = load_config(f.name)
            assert cfg.pack.version == "v1.0.0"
            assert cfg.pack.pack_name == "test-default"
            assert cfg.logging.level == "INFO"

            # Test with environment variables
            os.environ["PACK_VERSION"] = "v2.0.0"
            os.environ["ENV_NAME"] = "prod"
            os.environ["LOG_LEVEL"] = "DEBUG"

            cfg = load_config(f.name)
            assert cfg.pack.version == "v2.0.0"
            assert cfg.pack.pack_name == "test-prod"
            assert cfg.logging.level == "DEBUG"

        finally:
            os.unlink(f.name)
            # Clean up environment
            for key in ["PACK_VERSION", "ENV_NAME", "LOG_LEVEL"]:
                os.environ.pop(key, None)


def test_env_substitution_nested():
    """Test environment variable substitution in nested structures."""
    config_data = """
sign:
  key_ref: "${COSIGN_KEY_REF:-k8s://cosign/default}"
  provider: "${SIGN_PROVIDER:-cosign}"

metrics:
  sources: ["${METRICS_PATH:-bench/metrics}/**/*.json"]
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            # Test with default values
            cfg = load_config(f.name)
            assert cfg.sign.key_ref == "k8s://cosign/default"
            assert cfg.sign.provider == "cosign"
            assert "bench/metrics/**/*.json" in cfg.metrics.sources

            # Test with environment variables
            os.environ["COSIGN_KEY_REF"] = "k8s://cosign/prod"
            os.environ["SIGN_PROVIDER"] = "gpg"
            os.environ["METRICS_PATH"] = "prod/metrics"

            cfg = load_config(f.name)
            assert cfg.sign.key_ref == "k8s://cosign/prod"
            assert cfg.sign.provider == "gpg"
            assert "prod/metrics/**/*.json" in cfg.metrics.sources

        finally:
            os.unlink(f.name)
            # Clean up environment
            for key in ["COSIGN_KEY_REF", "SIGN_PROVIDER", "METRICS_PATH"]:
                os.environ.pop(key, None)


def test_env_substitution_in_profiles():
    """Test environment variable substitution in profiles."""
    config_data = """
pack:
  version: "v1.0.0"

profiles:
  hardening:
    sign:
      key_ref: "${COSIGN_KEY_REF:-k8s://cosign/hardening}"
      enabled: true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            # Test with default value
            cfg = load_config(f.name, env="hardening")
            assert cfg.sign.key_ref == "k8s://cosign/hardening"
            assert cfg.sign.enabled is True

            # Test with environment variable
            os.environ["COSIGN_KEY_REF"] = "k8s://cosign/prod"

            cfg = load_config(f.name, env="hardening")
            assert cfg.sign.key_ref == "k8s://cosign/prod"
            assert cfg.sign.enabled is True

        finally:
            os.unlink(f.name)
            # Clean up environment
            os.environ.pop("COSIGN_KEY_REF", None)


def test_pefc_env_prefix():
    """Test PEFC_ environment variable prefix."""
    config_data = """
pack:
  version: "v1.0.0"
  pack_name: "test"

logging:
  level: "INFO"
  json_mode: false
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_data)
        f.flush()

        try:
            # Test with PEFC_ prefixed environment variables
            os.environ["PEFC_PACK_VERSION"] = "v2.0.0"
            os.environ["PEFC_PACK_PACK_NAME"] = "env-override"
            os.environ["PEFC_LOGGING_LEVEL"] = "DEBUG"
            os.environ["PEFC_LOGGING_JSON_MODE"] = "true"

            cfg = load_config(f.name)
            assert cfg.pack.version == "v2.0.0"
            assert cfg.pack.pack_name == "env-override"
            assert cfg.logging.level == "DEBUG"
            assert cfg.logging.json_mode is True

        finally:
            os.unlink(f.name)
            # Clean up environment
            for key in [
                "PEFC_PACK_VERSION",
                "PEFC_PACK_PACK_NAME",
                "PEFC_LOGGING_LEVEL",
                "PEFC_LOGGING_JSON_MODE",
            ]:
                os.environ.pop(key, None)

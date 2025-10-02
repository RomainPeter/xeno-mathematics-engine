import os
from pathlib import Path

import yaml

from pefc.config.loader import clear_cache, expand_globs, get_config, load_config
from pefc.config.model import RootConfig


def test_load_default_config(tmp_path: Path):
    """Test loading default configuration."""
    # Créer un fichier de config minimal
    config_data = {
        "pack": {"version": "v1.0.0", "pack_name": "test-pack"},
        "metrics": {"sources": ["test/**/*.json"]},
    }

    config_file = tmp_path / "test.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_file)

    assert config.pack.version == "v1.0.0"
    assert config.pack.pack_name == "test-pack"
    assert config.metrics.sources == ["test/**/*.json"]
    assert config.metrics.include_aggregates is False  # default
    assert config.metrics.weight_key == "n_items"  # default


def test_env_overrides(tmp_path: Path):
    """Test that environment variables override config values."""
    # Créer un fichier de config
    config_data = {"pack": {"version": "v1.0.0", "pack_name": "test-pack"}}

    config_file = tmp_path / "test.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Set environment variables
    os.environ["PEFC_VERSION"] = "v2.0.0"
    os.environ["PEFC_PACK_NAME"] = "env-pack"
    os.environ["PEFC_LOG_LEVEL"] = "DEBUG"
    os.environ["PEFC_METRICS_INCLUDE_AGGREGATES"] = "true"

    try:
        config = load_config(config_file)

        assert config.pack.version == "v2.0.0"
        assert config.pack.pack_name == "env-pack"
        assert config.logging.level == "DEBUG"
        assert config.metrics.include_aggregates is True
    finally:
        # Clean up environment
        for key in [
            "PEFC_VERSION",
            "PEFC_PACK_NAME",
            "PEFC_LOG_LEVEL",
            "PEFC_METRICS_INCLUDE_AGGREGATES",
        ]:
            os.environ.pop(key, None)


def test_config_cache(tmp_path: Path):
    """Test that config caching works."""
    clear_cache()

    config_data = {"pack": {"version": "v1.0.0"}}
    config_file = tmp_path / "test.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # First call
    config1 = get_config(config_file, cache=True)
    # Second call should return cached version
    config2 = get_config(config_file, cache=True)

    assert config1 is config2  # Same object

    # Without cache should create new object
    config3 = get_config(config_file, cache=False)
    assert config3 is not config1


def test_expand_globs(tmp_path: Path):
    """Test glob pattern expansion."""
    # Créer des fichiers de test
    (tmp_path / "test1.json").write_text('{"test": 1}')
    (tmp_path / "test2.json").write_text('{"test": 2}')
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "test3.json").write_text('{"test": 3}')

    patterns = ["*.json", "subdir/*.json"]
    resolved = expand_globs(patterns, tmp_path)

    # Should find all JSON files
    assert len(resolved) >= 3
    assert any("test1.json" in str(p) for p in resolved)
    assert any("test2.json" in str(p) for p in resolved)
    assert any("test3.json" in str(p) for p in resolved)


def test_validation_strict_mode(tmp_path: Path):
    """Test that unknown keys are rejected."""
    config_data = {
        "pack": {"version": "v1.0.0"},
        "unknown_section": {"invalid": "value"},
    }

    config_file = tmp_path / "test.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    import pytest

    with pytest.raises(Exception):  # Pydantic validation error
        load_config(config_file)


def test_default_values():
    """Test that default values are applied correctly."""
    config = RootConfig()

    assert config.pack.version == "v0.1.0"
    assert config.pack.pack_name == "public-bench-pack"
    assert config.pack.out_dir == "dist"
    assert config.metrics.weight_key == "n_items"
    assert config.metrics.dedup == "first"
    assert config.logging.level == "INFO"
    assert config.logging.json_mode is False
    assert config.merkle.style == "v1"
    assert config.merkle.chunk_size == 1048576


def test_zip_name_formatting():
    """Test that zip_name formatting works with variables."""
    config = RootConfig()
    config.pack.pack_name = "test-pack"
    config.pack.version = "v1.2.3"
    config.pack.zip_name = "{pack_name}-{version}.zip"

    # This would be used in the actual implementation
    formatted = config.pack.zip_name.format(
        pack_name=config.pack.pack_name, version=config.pack.version
    )

    assert formatted == "test-pack-v1.2.3.zip"

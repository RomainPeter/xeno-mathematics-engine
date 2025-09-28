from __future__ import annotations
import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Union, Optional
from .model import RootConfig


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file and return parsed content."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge dictionary b into a."""
    result = a.copy()

    for key, value in b.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def expand_env(obj: Any) -> Any:
    """Recursively expand environment variables in strings."""
    if isinstance(obj, str):
        # Support ${VAR} and ${VAR:-default} patterns
        def replace_var(match):
            var_name = match.group(1)
            default = match.group(2) if match.group(2) else ""
            return os.getenv(var_name, default)

        return re.sub(r"\$\{([^:}]+)(?::-([^}]*))?\}", replace_var, obj)
    elif isinstance(obj, dict):
        return {k: expand_env(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_env(item) for item in obj]
    else:
        return obj


def normalize_paths(obj: Any, base_dir: Path) -> Any:
    """Normalize relative paths relative to base directory."""
    if isinstance(obj, str) and not Path(obj).is_absolute():
        # Only normalize if it looks like a path (contains / or ends with common extensions)
        if "/" in obj or obj.endswith((".json", ".yaml", ".yml", ".md", ".txt")):
            return str(base_dir / obj)
    elif isinstance(obj, dict):
        return {k: normalize_paths(v, base_dir) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_paths(item, base_dir) for item in obj]

    return obj


def get_active_env(env: Optional[str] = None) -> Optional[str]:
    """Get active environment from various sources."""
    if env:
        return env
    return os.getenv("PEFC_ENV")


def load_config(
    path: Union[str, Path], env: Optional[str] = None, env_prefix: str = "PEFC_"
) -> RootConfig:
    """Load configuration with environment overrides and validation."""
    config_path = Path(path)
    base_dir = config_path.parent

    # Load base configuration
    config_data = load_yaml(config_path)

    # Apply environment profile if specified
    active_env = get_active_env(env)
    if (
        active_env
        and "profiles" in config_data
        and active_env in config_data["profiles"]
    ):
        profile_data = config_data["profiles"][active_env]
        config_data = deep_merge(config_data, profile_data)

    # Apply environment variable overrides
    env_overrides = {}
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix) :].lower()
            # Handle nested keys like PEFC_PACK_VERSION -> pack.version
            if "_" in config_key:
                parts = config_key.split("_")
                if len(parts) >= 2:
                    section = parts[0]
                    field = "_".join(parts[1:])
                    if section not in env_overrides:
                        env_overrides[section] = {}
                    env_overrides[section][field] = value
            else:
                env_overrides[config_key] = value

    if env_overrides:
        config_data = deep_merge(config_data, env_overrides)

    # Expand environment variables in strings
    config_data = expand_env(config_data)

    # Normalize relative paths
    config_data = normalize_paths(config_data, base_dir)

    # Create and validate configuration
    config = RootConfig.model_validate(config_data)
    config._base_dir = str(base_dir)
    config._active_env = active_env

    return config

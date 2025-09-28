from __future__ import annotations
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .model import RootConfig

logger = logging.getLogger(__name__)

# Cache global pour éviter de recharger
_config_cache: Optional[RootConfig] = None


def load_config(path: Optional[Path] = None) -> RootConfig:
    """
    Charge la configuration depuis un fichier YAML.

    Priorité:
    1. CLI --config
    2. ENV PEFC_CONFIG
    3. config/pack.yaml (par défaut)
    """
    if path is None:
        # Vérifier ENV PEFC_CONFIG
        env_config = os.getenv("PEFC_CONFIG")
        if env_config:
            path = Path(env_config)
        else:
            # Par défaut
            path = Path("config/pack.yaml")

    if not path.exists():
        logger.warning(f"Config file not found: {path}, using defaults")
        return RootConfig()

    logger.info(f"Loading config from: {path}")

    # Charger YAML
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Appliquer les overrides ENV
    data = _apply_env_overrides(data)

    # Valider avec Pydantic
    config = RootConfig.model_validate(data)

    # Stocker le répertoire de base pour la résolution des chemins
    config._base_dir = path.parent

    return config


def get_config(path: Optional[Path] = None, cache: bool = True) -> RootConfig:
    """
    Récupère la configuration avec cache optionnel.
    """
    global _config_cache

    if cache and _config_cache is not None:
        return _config_cache

    config = load_config(path)

    if cache:
        _config_cache = config

    return config


def _apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applique les overrides depuis les variables d'environnement.
    """
    overrides = []

    # Pack overrides
    if "PEFC_VERSION" in os.environ:
        data.setdefault("pack", {})["version"] = os.environ["PEFC_VERSION"]
        overrides.append("PEFC_VERSION")

    if "PEFC_PACK_NAME" in os.environ:
        data.setdefault("pack", {})["pack_name"] = os.environ["PEFC_PACK_NAME"]
        overrides.append("PEFC_PACK_NAME")

    if "PEFC_OUT_DIR" in os.environ:
        data.setdefault("pack", {})["out_dir"] = os.environ["PEFC_OUT_DIR"]
        overrides.append("PEFC_OUT_DIR")

    # Logging overrides
    if "PEFC_LOG_LEVEL" in os.environ:
        data.setdefault("logging", {})["level"] = os.environ["PEFC_LOG_LEVEL"]
        overrides.append("PEFC_LOG_LEVEL")

    if "PEFC_LOG_JSON" in os.environ:
        data.setdefault("logging", {})["json_mode"] = os.environ[
            "PEFC_LOG_JSON"
        ].lower() in ("true", "1", "yes")
        overrides.append("PEFC_LOG_JSON")

    # Metrics overrides
    if "PEFC_METRICS_INCLUDE_AGGREGATES" in os.environ:
        data.setdefault("metrics", {})["include_aggregates"] = os.environ[
            "PEFC_METRICS_INCLUDE_AGGREGATES"
        ].lower() in ("true", "1", "yes")
        overrides.append("PEFC_METRICS_INCLUDE_AGGREGATES")

    if "PEFC_METRICS_WEIGHT_KEY" in os.environ:
        data.setdefault("metrics", {})["weight_key"] = os.environ[
            "PEFC_METRICS_WEIGHT_KEY"
        ]
        overrides.append("PEFC_METRICS_WEIGHT_KEY")

    if "PEFC_METRICS_DEDUP" in os.environ:
        dedup_value = os.environ["PEFC_METRICS_DEDUP"]
        if dedup_value in ("first", "last"):
            data.setdefault("metrics", {})["dedup"] = dedup_value
            overrides.append("PEFC_METRICS_DEDUP")

    if overrides:
        logger.info(f"Applied ENV overrides: {', '.join(overrides)}")

    return data


def expand_globs(patterns: list[str], base_dir: Path) -> list[Path]:
    """
    Résout les patterns glob relativement au répertoire de base.
    """
    from glob import glob

    resolved = []
    for pattern in patterns:
        # Résoudre relativement au répertoire de base
        full_pattern = base_dir / pattern
        matches = glob(str(full_pattern), recursive=True)
        resolved.extend(Path(m) for m in matches)

    return resolved


def clear_cache():
    """Efface le cache de configuration."""
    global _config_cache
    _config_cache = None

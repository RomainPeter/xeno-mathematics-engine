import json
from pathlib import Path

from pefc.config.loader import expand_globs, load_config
from pefc.summary import build_summary


def test_config_integration_with_build_summary(tmp_path: Path):
    """Test that config parameters are correctly passed to build_summary."""
    # Créer des fichiers de métriques de test
    (tmp_path / "metrics").mkdir()
    (tmp_path / "metrics" / "run1.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "group": "baseline",
                "n_items": 10,
                "metrics": {"coverage_gain": 0.5, "novelty_avg": 0.6},
            }
        )
    )
    (tmp_path / "metrics" / "run2.json").write_text(
        json.dumps(
            {
                "run_id": "r2",
                "group": "active",
                "n_items": 30,
                "metrics": {"coverage_gain": 0.9, "novelty_avg": 0.4},
            }
        )
    )

    # Créer un fichier de config
    config_data = {
        "pack": {"version": "v1.2.3", "pack_name": "test-integration-pack"},
        "metrics": {
            "sources": ["metrics/*.json"],
            "include_aggregates": False,
            "weight_key": "n_items",
            "dedup": "first",
            "bounded_metrics": ["coverage_gain", "novelty_avg"],
            "schema_path": "schema/summary.schema.json",
        },
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        import yaml

        yaml.dump(config_data, f)

    # Charger la config
    config = load_config(config_file)

    # Vérifier que les paramètres sont corrects
    assert config.pack.version == "v1.2.3"
    assert config.pack.pack_name == "test-integration-pack"
    assert config.metrics.weight_key == "n_items"
    assert config.metrics.dedup == "first"
    assert config.metrics.bounded_metrics == ["coverage_gain", "novelty_avg"]

    # Résoudre les sources
    sources = expand_globs(config.metrics.sources, config._base_dir)
    assert len(sources) == 2

    # Tester build_summary avec les paramètres de config
    output_path = tmp_path / "summary.json"
    result = build_summary(
        sources=sources,
        out_path=output_path,
        include_aggregates=config.metrics.include_aggregates,
        weight_key=config.metrics.weight_key,
        dedup=config.metrics.dedup,
        version=config.pack.version,
        validate=True,
        bounded_metrics=config.metrics.bounded_metrics,
        schema_path=Path(config.metrics.schema_path),
    )

    # Vérifier que le résultat contient les bonnes valeurs
    assert result["version"] == "v1.2.3"
    assert result["config"]["weight_key"] == "n_items"
    assert result["config"]["dedup"] == "first"
    assert len(result["runs"]) == 2

    # Vérifier que la validation a fonctionné (pas d'erreur)
    assert "overall" in result
    assert "by_group" in result


def test_zip_name_formatting_integration(tmp_path: Path):
    """Test that zip_name formatting works with config values."""
    config_data = {
        "pack": {
            "version": "v2.0.0",
            "pack_name": "integration-test",
            "zip_name": "{pack_name}-{version}-custom.zip",
        }
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        import yaml

        yaml.dump(config_data, f)

    config = load_config(config_file)

    # Simuler le formatage du nom de zip
    zip_name = config.pack.zip_name.format(
        pack_name=config.pack.pack_name, version=config.pack.version
    )

    assert zip_name == "integration-test-v2.0.0-custom.zip"


def test_config_with_relative_paths(tmp_path: Path):
    """Test that relative paths in config are resolved correctly."""
    # Créer une structure de répertoires
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "metrics").mkdir()
    (tmp_path / "data" / "metrics" / "test.json").write_text('{"test": 1}')

    # Config avec chemins relatifs
    config_data = {
        "pack": {"out_dir": "output"},
        "metrics": {"sources": ["data/metrics/*.json"]},
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        import yaml

        yaml.dump(config_data, f)

    config = load_config(config_file)

    # Vérifier que le répertoire de base est correct
    assert config._base_dir == tmp_path

    # Résoudre les sources
    sources = expand_globs(config.metrics.sources, config._base_dir)
    assert len(sources) == 1
    assert "test.json" in str(sources[0])

"""
Tests pour le pipeline 2cat - construction du pack.
"""

from pathlib import Path

import pytest

from xme.discovery_engine_2cat.config import (AEConfig, BudgetsConfig,
                                              CEGISConfig,
                                              DiscoveryEngine2CatConfig,
                                              OutputsConfig, PackConfig)
from xme.discovery_engine_2cat.runner import DiscoveryEngine2CatRunner
from xme.pefc.pack import verify_pack


@pytest.fixture
def temp_config(tmp_path: Path) -> DiscoveryEngine2CatConfig:
    """Fixture pour une configuration temporaire."""
    # Créer un contexte FCA minimal
    context_file = tmp_path / "context.json"
    context_data = {
        "attributes": ["attr1", "attr2"],
        "objects": [{"id": "obj1", "attrs": ["attr1"]}, {"id": "obj2", "attrs": ["attr2"]}],
    }
    import orjson

    with open(context_file, "wb") as f:
        f.write(orjson.dumps(context_data))

    # Créer la configuration
    config = DiscoveryEngine2CatConfig(
        ae=AEConfig(context=str(context_file)),
        cegis=CEGISConfig(secret="10", max_iters=4),
        budgets=BudgetsConfig(ae_ms=1000, cegis_ms=1000, total_ms=5000),
        outputs=OutputsConfig(
            psp=str(tmp_path / "artifacts" / "psp" / "2cat.json"),
            run_dir=str(tmp_path / "artifacts" / "pcap"),
            metrics=str(tmp_path / "artifacts" / "metrics" / "2cat.json"),
            report=str(tmp_path / "artifacts" / "reports" / "2cat.json"),
        ),
        pack=PackConfig(
            out=str(tmp_path / "dist"),
            include=["artifacts/psp/*.json", "artifacts/pcap/run-*.jsonl"],
            name="test-2cat-pack",
        ),
    )

    return config


@pytest.mark.asyncio
async def test_2cat_pipeline_builds_pack(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline 2cat construit un pack valide."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que le pipeline a réussi
    assert result["success"] is True
    assert "run_id" in result
    assert "artifacts" in result

    # Vérifier que le pack a été créé
    artifacts = result["artifacts"]
    assert "pack" in artifacts
    assert artifacts["pack"] is not None

    pack_path = Path(artifacts["pack"])
    assert pack_path.exists()
    assert pack_path.suffix == ".zip"

    # Vérifier l'intégrité du pack
    is_valid, message = verify_pack(pack_path)
    if not is_valid:
        print(f"Pack verification failed: {message}")
    assert is_valid is True, f"Pack verification failed: {message}"


@pytest.mark.asyncio
async def test_2cat_pipeline_generates_artifacts(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline génère tous les artefacts."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que tous les artefacts sont générés
    artifacts = result["artifacts"]

    # PSP
    assert "psp" in artifacts
    assert artifacts["psp"] is not None
    psp_path = Path(artifacts["psp"])
    assert psp_path.exists()
    assert psp_path.suffix == ".json"

    # PCAP
    assert "pcap" in artifacts
    assert artifacts["pcap"] is not None
    pcap_path = Path(artifacts["pcap"])
    assert pcap_path.exists()
    assert pcap_path.suffix == ".jsonl"

    # Métriques
    assert "metrics" in artifacts
    assert artifacts["metrics"] is not None
    metrics_path = Path(artifacts["metrics"])
    assert metrics_path.exists()
    assert metrics_path.suffix == ".json"

    # Pack
    assert "pack" in artifacts
    assert artifacts["pack"] is not None
    pack_path = Path(artifacts["pack"])
    assert pack_path.exists()
    assert pack_path.suffix == ".zip"


@pytest.mark.asyncio
async def test_2cat_pipeline_logs_pcap(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline logue correctement dans PCAP."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que PCAP contient les entrées attendues
    pcap_path = Path(result["artifacts"]["pcap"])
    assert pcap_path.exists()

    # Lire les entrées PCAP
    from xme.pcap.store import PCAPStore

    store = PCAPStore(pcap_path)
    entries = list(store.read_all())

    # Vérifier qu'il y a des entrées
    assert len(entries) > 0

    # Vérifier les actions attendues
    actions = [entry.get("action", "") for entry in entries]
    assert "2cat_pipeline_start" in actions
    assert "2cat_ae_start" in actions
    assert "2cat_cegis_start" in actions
    assert "2cat_pipeline_done" in actions


@pytest.mark.asyncio
async def test_2cat_pipeline_calculates_metrics(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline calcule les métriques."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que les métriques sont calculées
    results = result["results"]
    assert "metrics" in results
    assert "delta_run" in results["metrics"]

    # Vérifier que δ_run est borné
    delta_run = results["metrics"]["delta_run"]
    assert 0.0 <= delta_run <= 1.0

    # Vérifier que le fichier métriques existe
    metrics_path = Path(result["artifacts"]["metrics"])
    assert metrics_path.exists()

    # Vérifier le contenu du fichier métriques
    import orjson

    with open(metrics_path, "rb") as f:
        metrics_data = orjson.loads(f.read())

    assert "deltas" in metrics_data
    assert "delta_run" in metrics_data["deltas"]
    assert "total_entries" in metrics_data
    assert "summary" in metrics_data


@pytest.mark.asyncio
async def test_2cat_pipeline_verifies_psp(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline vérifie le PSP."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que la vérification a été effectuée
    results = result["results"]
    assert "verification" in results

    verification = results["verification"]
    assert "success" in verification
    assert "total_checks" in verification

    # Vérifier que le PSP est valide
    psp_path = Path(result["artifacts"]["psp"])
    assert psp_path.exists()

    # Charger et valider le PSP
    import orjson

    from xme.psp.schema import PSP

    with open(psp_path, "rb") as f:
        psp_data = orjson.loads(f.read())
    psp = PSP.model_validate(psp_data)
    assert len(psp.blocks) > 0
    assert len(psp.edges) >= 0


@pytest.mark.asyncio
async def test_2cat_pipeline_handles_errors(temp_config: DiscoveryEngine2CatConfig):
    """Test que le pipeline gère les erreurs."""
    # Modifier la configuration pour provoquer une erreur
    temp_config.ae.context = "nonexistent.json"

    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config)

    # Exécuter le pipeline (doit échouer)
    with pytest.raises(Exception):
        await runner.run()


@pytest.mark.asyncio
async def test_2cat_pipeline_config_validation():
    """Test la validation de la configuration."""
    # Configuration invalide
    invalid_config = DiscoveryEngine2CatConfig(
        ae=AEConfig(context="nonexistent.json"),
        cegis=CEGISConfig(secret="10"),
        budgets=BudgetsConfig(ae_ms=1000, cegis_ms=1000, total_ms=5000),
        outputs=OutputsConfig(),
        pack=PackConfig(),
    )

    # Valider la configuration
    errors = invalid_config.validate()
    assert len(errors) > 0
    assert any("not found" in error for error in errors)


def test_2cat_config_yaml_roundtrip(tmp_path: Path):
    """Test la sérialisation/désérialisation YAML."""
    # Créer une configuration
    config = DiscoveryEngine2CatConfig(
        ae=AEConfig(context="test.json"),
        cegis=CEGISConfig(secret="10"),
        budgets=BudgetsConfig(ae_ms=1000, cegis_ms=1000, total_ms=5000),
        outputs=OutputsConfig(),
        pack=PackConfig(),
    )

    # Sauvegarder en YAML
    yaml_path = tmp_path / "config.yaml"
    config.to_yaml(yaml_path)
    assert yaml_path.exists()

    # Recharger depuis YAML
    loaded_config = DiscoveryEngine2CatConfig.from_yaml(yaml_path)

    # Vérifier que les configurations sont identiques
    assert loaded_config.ae.context == config.ae.context
    assert loaded_config.cegis.secret == config.cegis.secret
    assert loaded_config.budgets.ae_ms == config.budgets.ae_ms

"""
Tests pour le pipeline 2cat - vérification PSP.
"""

import tempfile
from pathlib import Path

import pytest

from xme.discovery_engine_2cat.config import (AEConfig, BudgetsConfig,
                                              CEGISConfig,
                                              DiscoveryEngine2CatConfig,
                                              OutputsConfig, PackConfig)
from xme.discovery_engine_2cat.runner import DiscoveryEngine2CatRunner
from xme.verifier.base import Verifier, create_obligation
from xme.verifier.psp_checks import get_psp_obligations


@pytest.fixture
def temp_config_with_psp(tmp_path: Path) -> DiscoveryEngine2CatConfig:
    """Fixture pour une configuration avec PSP valide."""
    # Créer un contexte FCA qui génère un PSP valide
    context_file = tmp_path / "context.json"
    context_data = {
        "attributes": ["attr1", "attr2", "attr3"],
        "objects": [
            {"id": "obj1", "attrs": ["attr1", "attr2"]},
            {"id": "obj2", "attrs": ["attr1", "attr3"]},
            {"id": "obj3", "attrs": ["attr2", "attr3"]},
        ],
    }
    import orjson

    with open(context_file, "wb") as f:
        f.write(orjson.dumps(context_data))

    # Créer la configuration
    config = DiscoveryEngine2CatConfig(
        ae=AEConfig(context=str(context_file)),
        cegis=CEGISConfig(secret="101", max_iters=4),
        budgets=BudgetsConfig(ae_ms=2000, cegis_ms=2000, total_ms=8000),
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
async def test_2cat_pipeline_verifies_psp_s1(temp_config_with_psp: DiscoveryEngine2CatConfig):
    """Test que le pipeline vérifie le PSP avec les obligations S1."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config_with_psp)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que la vérification a été effectuée
    results = result["results"]
    assert "verification" in results

    verification = results["verification"]
    assert "success" in verification
    assert "total_checks" in verification
    assert "passed" in verification
    assert "failed" in verification

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

    # Vérifier que le PSP est un DAG
    assert psp.dag is not None
    assert psp.dag.number_of_nodes() == len(psp.blocks)
    assert len(psp.dag.edges) == len(psp.edges)


@pytest.mark.asyncio
async def test_2cat_pipeline_psp_verification_details(
    temp_config_with_psp: DiscoveryEngine2CatConfig,
):
    """Test que le pipeline fournit des détails de vérification."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config_with_psp)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que la vérification contient des détails
    verification = result["results"]["verification"]
    assert verification["success"] is True
    assert verification["total_checks"] > 0
    assert verification["passed"] > 0
    assert verification["failed"] == 0  # Toutes les vérifications doivent passer


@pytest.mark.asyncio
async def test_2cat_pipeline_psp_verification_logs_pcap(
    temp_config_with_psp: DiscoveryEngine2CatConfig,
):
    """Test que la vérification PSP est loguée dans PCAP."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config_with_psp)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que PCAP contient les logs de vérification
    pcap_path = Path(result["artifacts"]["pcap"])
    assert pcap_path.exists()

    # Lire les entrées PCAP
    from xme.pcap.store import PCAPStore

    store = PCAPStore(pcap_path)
    entries = list(store.read_all())

    # Vérifier les actions de vérification
    actions = [entry.get("action", "") for entry in entries]
    assert "2cat_verify_start" in actions
    assert "2cat_verify_done" in actions

    # Vérifier les verdicts de vérification
    verification_entries = [
        entry for entry in entries if entry.get("action") == "verification_verdict"
    ]
    assert len(verification_entries) > 0

    # Vérifier que les verdicts contiennent les obligations
    for entry in verification_entries:
        obligations = entry.get("obligations", {})
        assert len(obligations) > 0
        # Vérifier que les obligations contiennent des IDs de vérification
        obligation_ids = list(obligations.keys())
        assert any("psp_" in id for id in obligation_ids)


@pytest.mark.asyncio
async def test_2cat_pipeline_psp_verification_failure_handling():
    """Test la gestion des échecs de vérification PSP."""
    # Créer une configuration qui génère un PSP invalide
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Créer un contexte FCA qui génère un PSP avec des problèmes
        context_file = tmp_path / "context.json"
        context_data = {"attributes": ["attr1"], "objects": [{"id": "obj1", "attrs": ["attr1"]}]}
        import orjson

        with open(context_file, "wb") as f:
            f.write(orjson.dumps(context_data))

        # Créer la configuration
        config = DiscoveryEngine2CatConfig(
            ae=AEConfig(context=str(context_file)),
            cegis=CEGISConfig(secret="1", max_iters=2),
            budgets=BudgetsConfig(ae_ms=1000, cegis_ms=1000, total_ms=4000),
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

        # Créer le runner
        runner = DiscoveryEngine2CatRunner(config)

        # Exécuter le pipeline
        result = await runner.run()

        # Vérifier que la vérification a été effectuée
        verification = result["results"]["verification"]
        assert "success" in verification
        # Le résultat peut être True ou False selon le PSP généré


@pytest.mark.asyncio
async def test_2cat_pipeline_psp_verification_obligations_coverage(
    temp_config_with_psp: DiscoveryEngine2CatConfig,
):
    """Test que la vérification PSP couvre toutes les obligations."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config_with_psp)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que PCAP contient les verdicts de toutes les obligations
    pcap_path = Path(result["artifacts"]["pcap"])
    from xme.pcap.store import PCAPStore

    store = PCAPStore(pcap_path)
    entries = list(store.read_all())

    # Extraire les obligations vérifiées
    verified_obligations = set()
    for entry in entries:
        if entry.get("action") == "verification_verdict":
            obligations = entry.get("obligations", {})
            for obligation_id in obligations.keys():
                if not obligation_id.endswith("_message") and not obligation_id.endswith("_error"):
                    verified_obligations.add(obligation_id)

    # Vérifier que les obligations PSP sont couvertes (au moins quelques-unes)
    psp_obligations = [obligation_id for obligation_id, _, _, _ in get_psp_obligations()]
    verified_count = sum(
        1 for obligation_id in psp_obligations if obligation_id in verified_obligations
    )
    assert (
        verified_count >= 1
    ), f"Only {verified_count} PSP obligations verified, expected at least 1"


@pytest.mark.asyncio
async def test_2cat_pipeline_psp_verification_s1_level(
    temp_config_with_psp: DiscoveryEngine2CatConfig,
):
    """Test que la vérification PSP utilise le niveau S1."""
    # Créer le runner
    runner = DiscoveryEngine2CatRunner(temp_config_with_psp)

    # Exécuter le pipeline
    result = await runner.run()

    # Vérifier que PCAP contient les verdicts S1
    pcap_path = Path(result["artifacts"]["pcap"])
    from xme.pcap.store import PCAPStore

    store = PCAPStore(pcap_path)
    entries = list(store.read_all())

    # Vérifier que les verdicts contiennent des niveaux S1
    s1_verdicts = []
    for entry in entries:
        if entry.get("action") == "verification_verdict":
            level = entry.get("level", "")
            if level == "S1":
                s1_verdicts.append(entry)

    assert len(s1_verdicts) > 0, "No S1 level verdicts found"

    # Vérifier que les obligations S1 sont présentes
    s1_obligations = [
        obligation_id for obligation_id, level, _, _ in get_psp_obligations() if level == "S1"
    ]
    verified_s1_obligations = set()
    for entry in s1_verdicts:
        obligations = entry.get("obligations", {})
        for obligation_id in obligations.keys():
            if not obligation_id.endswith("_message") and not obligation_id.endswith("_error"):
                verified_s1_obligations.add(obligation_id)

    for obligation_id in s1_obligations:
        assert (
            obligation_id in verified_s1_obligations
        ), f"S1 obligation {obligation_id} not verified"


def test_2cat_pipeline_psp_verification_standalone():
    """Test la vérification PSP en mode standalone."""
    # Créer un PSP valide
    from xme.psp.schema import PSP, Block, Edge

    psp = PSP(
        blocks=[
            Block(id="block1", kind="axiom", content="A"),
            Block(id="block2", kind="lemma", content="B"),
            Block(id="block3", kind="theorem", content="C"),
        ],
        edges=[Edge(src="block1", dst="block2"), Edge(src="block2", dst="block3")],
    )

    # Créer le vérificateur
    verifier = Verifier()
    for obligation_id, level, check_func, description in get_psp_obligations():
        obligation = create_obligation(obligation_id, level, check_func, description)
        verifier.register_obligation(obligation)

    # Exécuter les vérifications S1
    report = verifier.run_by_level(psp.model_dump(), "S1")

    # Vérifier que toutes les vérifications passent
    assert report.ok_all is True
    assert len(report.results) > 0

    # Vérifier que les obligations S1 sont présentes
    s1_results = [r for r in report.results if r.level == "S1"]
    assert len(s1_results) > 0

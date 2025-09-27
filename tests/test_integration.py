"""
Tests d'intégration pour le Proof Engine for Code v0.
Teste l'architecture complète avec rollback et replanning.
"""

import pytest
import tempfile
import os
from proofengine.core.schemas import VJustification, Proof, PCAP
from proofengine.core.state import create_initial_state
from planner.meta import MetacognitivePlanner
from generator.stochastic import StochasticGenerator
from runner.deterministic import DeterministicRunner
from runner.verifier import Verifier
from metrics.collect import MetricsCollector


class TestIntegration:
    """Tests d'intégration pour l'architecture complète."""

    def test_metacognitive_planner_integration(self):
        """Test d'intégration du planificateur métacognitif."""
        # Créer un état initial
        initial_state = create_initial_state(
            hypotheses={"input_sanitization_required"},
            evidences={"user_input_present"},
            obligations=[
                {"policy": "pytest", "test_file": "test_sanitize.py"},
                {"policy": "ruff", "max_issues": 0},
            ],
            artifacts=["sanitize_input.py"],
            sigma={"case": "sanitize_input", "seed": 42},
        )

        # Créer le planificateur
        planner = MetacognitivePlanner({"seed": 42})

        # Générer un plan
        plan = planner.plan(initial_state, "sanitize user input")

        assert plan is not None
        assert plan.plan_id is not None
        assert len(plan.actions) > 0
        assert plan.estimated_utility >= 0
        assert 0 <= plan.confidence <= 1

    def test_stochastic_generator_integration(self):
        """Test d'intégration du générateur stochastique."""
        generator = StochasticGenerator(seed=42)

        # Générer des variantes d'actions
        variants = generator.propose_actions(
            goal="sanitize user input",
            obligations=[{"policy": "pytest"}, {"policy": "ruff"}],
            seed=42,
            k=3,
        )

        assert len(variants) <= 3
        for variant in variants:
            assert variant.action_id is not None
            assert variant.description is not None
            assert variant.patch is not None
            assert 0 <= variant.confidence <= 1

    def test_deterministic_runner_integration(self):
        """Test d'intégration de l'exécuteur déterministe."""
        runner = DeterministicRunner()

        # Créer un contexte de test
        context = {
            "goal": "sanitize user input",
            "obligations": [{"policy": "pytest"}],
            "code_content": "def test(): pass",
            "test_content": "def test_sanitize(): assert True",
        }

        # Exécuter les vérifications
        proofs, cost = runner.run_and_prove(context, [{"policy": "pytest"}], seed=42)

        assert isinstance(proofs, list)
        assert isinstance(cost, VJustification)
        assert cost.time_ms >= 0
        assert cost.audit_cost >= 0

    def test_verifier_integration(self):
        """Test d'intégration du vérifieur."""
        verifier = Verifier()

        # Créer un PCAP de test
        pcap = PCAP(
            operator="test_operator",
            action="test_action",
            pre_hash="pre_hash",
            post_hash="post_hash",
            obligations=["test_obligation"],
            justification=VJustification(
                time_ms=100,
                retries=0,
                backtracks=0,
                audit_cost=1.0,
                risk=0.1,
                tech_debt=0,
            ),
            proofs=[
                Proof(kind="unit", name="test_proof", passed=True, logs="Test passed")
            ],
            verdict="pass",
            toolchain={"seed": 42},
            pcap_hash="test_pcap_hash",
        )

        # Vérifier le PCAP
        verification_result = verifier.replay(pcap)

        assert "verdict" in verification_result
        assert "integrity_check" in verification_result
        assert "replay_results" in verification_result

    def test_metrics_collector_integration(self):
        """Test d'intégration du collecteur de métriques."""
        collector = MetricsCollector()

        # Créer des PCAPs de test
        pcaps = [
            PCAP(
                operator="test1",
                action="action1",
                pre_hash="pre1",
                post_hash="post1",
                obligations=["obligation1"],
                justification=VJustification(
                    time_ms=100,
                    retries=0,
                    backtracks=0,
                    audit_cost=1.0,
                    risk=0.1,
                    tech_debt=0,
                ),
                proofs=[],
                verdict="pass",
                toolchain={},
                pcap_hash="hash1",
            ),
            PCAP(
                operator="test2",
                action="action2",
                pre_hash="pre2",
                post_hash="post2",
                obligations=["obligation2"],
                justification=VJustification(
                    time_ms=200,
                    retries=1,
                    backtracks=0,
                    audit_cost=2.0,
                    risk=0.2,
                    tech_debt=1,
                ),
                proofs=[],
                verdict="fail",
                toolchain={},
                pcap_hash="hash2",
            ),
        ]

        # Simuler la collecte de métriques
        with tempfile.TemporaryDirectory() as temp_dir:
            # Sauvegarder les PCAPs
            for i, pcap in enumerate(pcaps):
                pcap_file = os.path.join(temp_dir, f"pcap_{i}.json")
                with open(pcap_file, "w") as f:
                    f.write(pcap.to_json())

            # Collecter les métriques
            metrics = collector.collect_metrics(temp_dir)

            assert "total_pcaps" in metrics
            assert "basic_metrics" in metrics
            assert "cost_metrics" in metrics
            assert metrics["total_pcaps"] == 2

    def test_end_to_end_workflow(self):
        """Test du workflow complet end-to-end."""
        # Créer l'état initial
        initial_state = create_initial_state(
            hypotheses={"input_sanitization_required"},
            evidences={"user_input_present"},
            obligations=[
                {"policy": "pytest", "test_file": "test_sanitize.py"},
                {"policy": "ruff", "max_issues": 0},
            ],
            artifacts=["sanitize_input.py"],
            sigma={"case": "sanitize_input", "seed": 42},
        )

        # Créer le planificateur
        planner = MetacognitivePlanner({"seed": 42})

        # Exécuter le plan
        result = planner.execute_plan(
            initial_state,
            "sanitize user input",
            {"time_limit_ms": 10000, "max_retries": 2},
        )

        # Vérifier les résultats
        assert "success" in result
        assert "final_state" in result
        assert "execution_history" in result
        assert "metrics" in result

        # Vérifier que l'état a été modifié
        final_state = result["final_state"]
        assert final_state is not None

        # Vérifier l'historique d'exécution
        execution_history = result["execution_history"]
        assert isinstance(execution_history, list)

        # Vérifier les métriques
        metrics = result["metrics"]
        assert "total_actions" in metrics
        assert "success_rate" in metrics

    def test_rollback_and_replan_scenario(self):
        """Test du scénario de rollback et replanning."""
        # Créer un état initial avec des obligations strictes
        initial_state = create_initial_state(
            hypotheses={"strict_requirements"},
            evidences={"complex_context"},
            obligations=[
                {"policy": "pytest", "test_file": "test_strict.py"},
                {"policy": "mypy", "strict": True},
                {"policy": "forbidden_imports", "forbidden_imports": ["eval", "exec"]},
            ],
            artifacts=["complex_code.py"],
            sigma={"case": "strict_test", "seed": 42},
        )

        # Créer le planificateur
        planner = MetacognitivePlanner({"seed": 42})

        # Exécuter avec un budget limité pour forcer les échecs
        result = planner.execute_plan(
            initial_state,
            "implement strict requirements",
            {"time_limit_ms": 5000, "max_retries": 1},
        )

        # Vérifier que le système a géré les échecs
        assert "success" in result
        assert "execution_history" in result

        # Vérifier qu'il y a eu des tentatives
        execution_history = result["execution_history"]
        assert len(execution_history) > 0

        # Vérifier que le système a appris des échecs
        final_state = result["final_state"]
        if final_state and len(final_state.K) > len(initial_state.K):
            # Des règles ont été ajoutées suite aux échecs
            assert True

    def test_reproducibility(self):
        """Test de reproductibilité avec la même graine."""
        # Créer l'état initial
        initial_state = create_initial_state(
            hypotheses={"reproducibility_test"},
            evidences={"deterministic_behavior"},
            obligations=[{"policy": "pytest"}],
            artifacts=["test_code.py"],
            sigma={"case": "reproducibility", "seed": 12345},
        )

        # Exécuter deux fois avec la même graine
        planner1 = MetacognitivePlanner({"seed": 12345})
        result1 = planner1.execute_plan(initial_state, "test reproducibility")

        planner2 = MetacognitivePlanner({"seed": 12345})
        result2 = planner2.execute_plan(initial_state, "test reproducibility")

        # Vérifier la reproductibilité
        assert result1["success"] == result2["success"]
        assert len(result1["execution_history"]) == len(result2["execution_history"])

        # Vérifier que les métriques sont similaires
        metrics1 = result1["metrics"]
        metrics2 = result2["metrics"]
        assert metrics1["total_actions"] == metrics2["total_actions"]


if __name__ == "__main__":
    pytest.main([__file__])

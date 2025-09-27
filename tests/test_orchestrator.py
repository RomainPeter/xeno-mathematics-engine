"""
Tests pour l'orchestrateur principal.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from cli import ProofEngineOrchestrator


class TestProofEngineOrchestrator:
    """Tests pour l'orchestrateur principal."""

    def test_orchestrator_initialization(self):
        """Test d'initialisation de l'orchestrateur."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            assert orchestrator.base_dir == temp_dir
            assert orchestrator.output_dir == "out"
            assert orchestrator.pcap_dir == "out/pcap"
            assert orchestrator.metrics_dir == "out/metrics"
            assert orchestrator.audit_dir == "out/audit"

            # Vérifier que les répertoires sont créés
            assert os.path.exists("out/pcap")
            assert os.path.exists("out/metrics")
            assert os.path.exists("out/audit")

    def test_create_initial_state(self):
        """Test de création de l'état initial."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            state = orchestrator._create_initial_state("test_case", "test goal")

            assert state.H == ["goal:test goal"]
            assert state.K == [
                "tests_ok",
                "lint_ok",
                "types_ok",
                "security_ok",
                "complexity_ok",
                "docstring_ok",
            ]
            assert state.Sigma["case_id"] == "test_case"
            assert "timestamp" in state.Sigma

    def test_execute_planning_phase_success(self):
        """Test de la phase de planification réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")
            orchestrator.current_state = orchestrator._create_initial_state(
                "test_case", "test goal"
            )

            with patch.object(orchestrator.planner, "propose_plan") as mock_plan:
                mock_plan.return_value = MagicMock(
                    plan=["step1", "step2"],
                    est_success=0.8,
                    est_cost=2.0,
                    notes="Test plan",
                    llm_meta={"latency_ms": 1000, "model": "x-ai/grok-4-fast:free"},
                )

                with patch("core.pcap.write_pcap") as mock_write:
                    result = orchestrator._execute_planning_phase("test goal")

                    assert result["success"] == True
                    assert result["plan"] == ["step1", "step2"]
                    assert result["estimated_success"] == 0.8
                    assert result["estimated_cost"] == 2.0
                    assert result["notes"] == "Test plan"

    def test_execute_planning_phase_failure(self):
        """Test de la phase de planification échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")
            orchestrator.current_state = orchestrator._create_initial_state(
                "test_case", "test goal"
            )

            with patch.object(orchestrator.planner, "propose_plan") as mock_plan:
                mock_plan.side_effect = Exception("Planning failed")

                result = orchestrator._execute_planning_phase("test goal")

                assert result["success"] == False
                assert "error" in result
                assert result["plan"] == []
                assert result["estimated_success"] == 0.0

    def test_execute_generation_phase_success(self):
        """Test de la phase de génération réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")
            orchestrator.current_state = orchestrator._create_initial_state(
                "test_case", "test goal"
            )

            with patch.object(
                orchestrator.generator, "propose_variants"
            ) as mock_variants:
                mock_variants.return_value = [
                    MagicMock(
                        patch_unified="patch1",
                        rationale="Test patch 1",
                        predicted_obligations_satisfied=["tests_ok"],
                        risk_score=0.3,
                        notes="Test notes 1",
                        llm_meta={"latency_ms": 500},
                    ),
                    MagicMock(
                        patch_unified="patch2",
                        rationale="Test patch 2",
                        predicted_obligations_satisfied=["tests_ok", "lint_ok"],
                        risk_score=0.2,
                        notes="Test notes 2",
                        llm_meta={"latency_ms": 600},
                    ),
                ]

                with patch.object(
                    orchestrator.controller, "evaluate_patch"
                ) as mock_eval:
                    mock_eval.side_effect = [
                        {"success": False, "violations": 2},
                        {"success": True, "violations": 0},
                    ]

                    with patch("core.pcap.write_pcap") as mock_write:
                        result = orchestrator._execute_generation_phase("test goal")

                        assert result["success"] == True
                        assert result["best_patch"] == "patch2"
                        assert result["best_result"]["success"] == True
                        assert result["best_result"]["violations"] == 0
                        assert result["best_index"] == 1
                        assert result["total_variants"] == 2

    def test_execute_generation_phase_failure(self):
        """Test de la phase de génération échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")
            orchestrator.current_state = orchestrator._create_initial_state(
                "test_case", "test goal"
            )

            with patch.object(
                orchestrator.generator, "propose_variants"
            ) as mock_variants:
                mock_variants.return_value = [
                    MagicMock(
                        patch_unified="patch1",
                        rationale="Test patch 1",
                        predicted_obligations_satisfied=["tests_ok"],
                        risk_score=0.3,
                        notes="Test notes 1",
                        llm_meta={"latency_ms": 500},
                    )
                ]

                with patch.object(
                    orchestrator.controller, "evaluate_patch"
                ) as mock_eval:
                    mock_eval.return_value = {"success": False, "violations": 3}

                    with patch.object(
                        orchestrator, "_execute_rollback_phase"
                    ) as mock_rollback:
                        mock_rollback.return_value = {
                            "success": False,
                            "rollback": True,
                            "replan": ["new step1", "new step2"],
                        }

                        result = orchestrator._execute_generation_phase("test goal")

                        assert result["success"] == False
                        assert result["rollback"] == True
                        assert "replan" in result

    def test_execute_rollback_phase(self):
        """Test de la phase de rollback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")
            orchestrator.current_state = orchestrator._create_initial_state(
                "test_case", "test goal"
            )

            with patch.object(
                orchestrator.planner, "replan_after_failure"
            ) as mock_replan:
                mock_replan.return_value = MagicMock(
                    plan=["new step1", "new step2"],
                    est_success=0.6,
                    est_cost=3.0,
                    notes="Replan after failure",
                    llm_meta={"latency_ms": 800},
                )

                with patch("core.pcap.write_pcap") as mock_write:
                    result = orchestrator._execute_rollback_phase("test goal")

                    assert result["success"] == False
                    assert result["rollback"] == True
                    assert result["replan"] == ["new step1", "new step2"]
                    assert result["estimated_success"] == 0.6
                    assert result["notes"] == "Replan after failure"

    def test_execute_verification_phase(self):
        """Test de la phase de vérification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            with patch("verifier.runner.verify_pcap_dir") as mock_verify:
                mock_verify.return_value = {
                    "attestation": {"ts": 1234567890, "pcap_count": 3},
                    "chain_verification": {"status": "ok", "count": 3},
                    "attestation_file": "out/audit/attestation.json",
                }

                result = orchestrator._execute_verification_phase()

                assert result["success"] == True
                assert "verification" in result
                assert "attestation_file" in result

    def test_execute_metrics_phase(self):
        """Test de la phase de métriques."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            with patch.object(
                orchestrator.metrics_collector, "collect_metrics"
            ) as mock_collect:
                mock_collect.return_value = {
                    "total_pcaps": 5,
                    "basic_metrics": {"success_rate": 0.8},
                    "performance_metrics": {"average_time_ms": 1000},
                }

                with patch.object(
                    orchestrator.report_generator, "save_report"
                ) as mock_report:
                    mock_report.side_effect = [
                        "out/metrics/report.md",
                        "out/metrics/report.json",
                    ]

                    result = orchestrator._execute_metrics_phase()

                    assert result["success"] == True
                    assert "metrics" in result
                    assert "markdown_report" in result
                    assert "json_report" in result

    def test_run_demo_success(self):
        """Test de la démonstration complète réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            with patch.object(orchestrator, "_execute_planning_phase") as mock_plan:
                mock_plan.return_value = {"success": True, "plan": ["step1", "step2"]}

                with patch.object(
                    orchestrator, "_execute_generation_phase"
                ) as mock_gen:
                    mock_gen.return_value = {
                        "success": True,
                        "best_patch": "test patch",
                        "violations": 0,
                    }

                    with patch.object(
                        orchestrator, "_execute_verification_phase"
                    ) as mock_verify:
                        mock_verify.return_value = {"success": True}

                        with patch.object(
                            orchestrator, "_execute_metrics_phase"
                        ) as mock_metrics:
                            mock_metrics.return_value = {"success": True}

                            result = orchestrator.run_demo("test_case", "test goal")

                            assert result["success"] == True
                            assert result["case_id"] == "test_case"
                            assert result["goal"] == "test goal"
                            assert "planning" in result
                            assert "generation" in result
                            assert "verification" in result
                            assert "metrics" in result
                            assert "execution_time_ms" in result

    def test_run_demo_failure(self):
        """Test de la démonstration complète échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            with patch.object(orchestrator, "_execute_planning_phase") as mock_plan:
                mock_plan.return_value = {"success": True, "plan": ["step1", "step2"]}

                with patch.object(
                    orchestrator, "_execute_generation_phase"
                ) as mock_gen:
                    mock_gen.return_value = {
                        "success": False,
                        "rollback": True,
                        "replan": ["new step1"],
                    }

                    with patch.object(
                        orchestrator, "_execute_verification_phase"
                    ) as mock_verify:
                        mock_verify.return_value = {"success": True}

                        with patch.object(
                            orchestrator, "_execute_metrics_phase"
                        ) as mock_metrics:
                            mock_metrics.return_value = {"success": True}

                            result = orchestrator.run_demo("test_case", "test goal")

                            assert result["success"] == False
                            assert result["case_id"] == "test_case"
                            assert result["goal"] == "test goal"
                            assert "planning" in result
                            assert "generation" in result
                            assert "verification" in result
                            assert "metrics" in result


class TestOrchestratorIntegration:
    """Tests d'intégration pour l'orchestrateur."""

    def test_full_workflow_integration(self):
        """Test d'intégration du workflow complet."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier de test simple
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write('print("hello")\n')

            orchestrator = ProofEngineOrchestrator(temp_dir, "out")

            # Mock de tous les composants
            with patch.object(orchestrator.planner, "propose_plan") as mock_plan:
                with patch.object(
                    orchestrator.generator, "propose_variants"
                ) as mock_variants:
                    with patch.object(
                        orchestrator.controller, "evaluate_patch"
                    ) as mock_eval:
                        with patch("verifier.runner.verify_pcap_dir") as mock_verify:
                            with patch.object(
                                orchestrator.metrics_collector, "collect_metrics"
                            ) as mock_collect:
                                with patch.object(
                                    orchestrator.report_generator, "save_report"
                                ) as mock_report:
                                    # Configuration des mocks
                                    mock_plan.return_value = MagicMock(
                                        plan=["step1", "step2"],
                                        est_success=0.8,
                                        est_cost=2.0,
                                        notes="Test plan",
                                        llm_meta={"latency_ms": 1000},
                                    )

                                    mock_variants.return_value = [
                                        MagicMock(
                                            patch_unified="test patch",
                                            rationale="Test rationale",
                                            predicted_obligations_satisfied=[
                                                "tests_ok"
                                            ],
                                            risk_score=0.3,
                                            notes="Test notes",
                                            llm_meta={"latency_ms": 500},
                                        )
                                    ]

                                    mock_eval.return_value = {
                                        "success": True,
                                        "violations": 0,
                                        "obligation_results": MagicMock(),
                                        "delta_metrics": {"delta_total": 0.1},
                                        "justification": MagicMock(),
                                        "evaluation_time_ms": 1000,
                                    }

                                    mock_verify.return_value = {
                                        "attestation": {
                                            "ts": 1234567890,
                                            "pcap_count": 3,
                                        },
                                        "chain_verification": {
                                            "status": "ok",
                                            "count": 3,
                                        },
                                        "attestation_file": "out/audit/attestation.json",
                                    }

                                    mock_collect.return_value = {
                                        "total_pcaps": 3,
                                        "basic_metrics": {"success_rate": 1.0},
                                        "performance_metrics": {
                                            "average_time_ms": 1000
                                        },
                                    }

                                    mock_report.side_effect = [
                                        "out/metrics/report.md",
                                        "out/metrics/report.json",
                                    ]

                                    # Exécuter la démonstration
                                    result = orchestrator.run_demo(
                                        "test_case", "test goal"
                                    )

                                    # Vérifier les résultats
                                    assert result["success"] == True
                                    assert result["case_id"] == "test_case"
                                    assert result["goal"] == "test goal"
                                    assert "planning" in result
                                    assert "generation" in result
                                    assert "verification" in result
                                    assert "metrics" in result
                                    assert "execution_time_ms" in result

                                    # Vérifier que les composants ont été appelés
                                    mock_plan.assert_called_once()
                                    mock_variants.assert_called_once()
                                    mock_eval.assert_called_once()
                                    mock_verify.assert_called_once()
                                    mock_collect.assert_called_once()
                                    mock_report.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])

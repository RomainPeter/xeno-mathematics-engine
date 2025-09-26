"""
Tests pour le contrôleur déterministe.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from controller.obligations import (
    check_tests, check_flake8, check_mypy, check_bandit,
    check_complexity, check_docstrings, evaluate_obligations,
    get_obligation_details, get_violation_summary
)
from controller.patch import Workspace, PatchManager
from controller.deterministic import DeterministicController
from proofengine.core.schemas import ObligationResults


class TestObligations:
    """Tests pour les vérifications d'obligations."""
    
    def test_check_tests_success(self):
        """Test de vérification des tests réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier de test simple
            test_file = os.path.join(temp_dir, "test_example.py")
            with open(test_file, 'w') as f:
                f.write("""
def test_example():
    assert True
""")
            
            # Mock de pytest
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, "test passed", "")
                result = check_tests(temp_dir)
                assert result == True
    
    def test_check_tests_failure(self):
        """Test de vérification des tests échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (1, "", "test failed")
                result = check_tests(temp_dir)
                assert result == False
    
    def test_check_flake8_success(self):
        """Test de vérification flake8 réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, "", "")
                result = check_flake8(temp_dir)
                assert result == True
    
    def test_check_flake8_failure(self):
        """Test de vérification flake8 échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (1, "", "E501 line too long")
                result = check_flake8(temp_dir)
                assert result == False
    
    def test_check_mypy_success(self):
        """Test de vérification mypy réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, "", "")
                result = check_mypy(temp_dir)
                assert result == True
    
    def test_check_mypy_failure(self):
        """Test de vérification mypy échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (1, "", "error: Incompatible types")
                result = check_mypy(temp_dir)
                assert result == False
    
    def test_check_bandit_success(self):
        """Test de vérification bandit réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, "", "")
                result = check_bandit(temp_dir)
                assert result == True
    
    def test_check_bandit_failure(self):
        """Test de vérification bandit échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (1, "", "B101: Use of assert detected")
                result = check_bandit(temp_dir)
                assert result == False
    
    def test_check_complexity_success(self):
        """Test de vérification de complexité réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, '{"file.py": [{"complexity": 5}]}', "")
                result = check_complexity(temp_dir, max_cc=10)
                assert result == True
    
    def test_check_complexity_failure(self):
        """Test de vérification de complexité échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                mock_run.return_value = (0, '{"file.py": [{"complexity": 15}]}', "")
                result = check_complexity(temp_dir, max_cc=10)
                assert result == False
    
    def test_check_docstrings_success(self):
        """Test de vérification des docstrings réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier avec docstring
            test_file = os.path.join(temp_dir, "example.py")
            with open(test_file, 'w') as f:
                f.write('"""Module docstring."""\n\ndef function():\n    pass\n')
            
            result = check_docstrings(temp_dir)
            assert result == True
    
    def test_check_docstrings_failure(self):
        """Test de vérification des docstrings échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier sans docstring
            test_file = os.path.join(temp_dir, "example.py")
            with open(test_file, 'w') as f:
                f.write('def function():\n    pass\n')
            
            result = check_docstrings(temp_dir)
            assert result == False
    
    def test_evaluate_obligations(self):
        """Test d'évaluation complète des obligations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('controller.obligations.run_command') as mock_run:
                # Mock de toutes les vérifications
                mock_run.return_value = (0, "", "")
                
                result = evaluate_obligations(temp_dir)
                
                assert isinstance(result, ObligationResults)
                assert result.tests_ok == True
                assert result.lint_ok == True
                assert result.types_ok == True
                assert result.security_ok == True
                assert result.complexity_ok == True
                assert result.docstring_ok == True
    
    def test_get_violation_summary(self):
        """Test du résumé des violations."""
        results = ObligationResults(
            tests_ok=True,
            lint_ok=False,
            types_ok=True,
            security_ok=False,
            complexity_ok=True,
            docstring_ok=False
        )
        
        summary = get_violation_summary(results)
        
        assert summary["total_violations"] == 3
        assert "lint_ok" in summary["violations"]
        assert "security_ok" in summary["violations"]
        assert "docstring_ok" in summary["violations"]
        assert summary["all_passed"] == False
        assert summary["success_rate"] == 0.5


class TestWorkspace:
    """Tests pour la classe Workspace."""
    
    def test_workspace_creation(self):
        """Test de création d'un workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier de base
            base_file = os.path.join(temp_dir, "test.py")
            with open(base_file, 'w') as f:
                f.write('print("hello")\n')
            
            workspace = Workspace(temp_dir)
            
            assert workspace.base_dir == temp_dir
            assert os.path.exists(workspace.work_dir)
            assert workspace.work_dir != temp_dir
    
    def test_apply_unified_diff_success(self):
        """Test d'application d'un patch unifié réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Créer un fichier de base
            base_file = os.path.join(temp_dir, "test.py")
            with open(base_file, 'w') as f:
                f.write('print("hello")\n')
            
            workspace = Workspace(temp_dir)
            
            # Patch simple
            patch_text = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print("hello")
+print("world")
"""
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = workspace.apply_unified_diff(patch_text)
                assert result == True
    
    def test_apply_unified_diff_failure(self):
        """Test d'application d'un patch unifié échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Workspace(temp_dir)
            
            # Patch invalide
            patch_text = "invalid patch"
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Patch failed")
                result = workspace.apply_unified_diff(patch_text)
                assert result == False
    
    def test_get_changed_files(self):
        """Test de récupération des fichiers modifiés."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Workspace(temp_dir)
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="file1.py\nfile2.py\n"
                )
                
                changed_files = workspace.get_changed_files()
                assert "file1.py" in changed_files
                assert "file2.py" in changed_files
    
    def test_cleanup(self):
        """Test de nettoyage du workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Workspace(temp_dir)
            work_dir = workspace.work_dir
            
            assert os.path.exists(work_dir)
            
            workspace.cleanup()
            
            # Le répertoire devrait être supprimé
            assert not os.path.exists(work_dir)


class TestPatchManager:
    """Tests pour la classe PatchManager."""
    
    def test_validate_patch_valid(self):
        """Test de validation d'un patch valide."""
        manager = PatchManager()
        
        patch_text = """--- file.py
+++ file.py
@@ -1,1 +1,1 @@
-old line
+new line
"""
        
        result = manager.validate_patch(patch_text)
        assert result["valid"] == True
        assert len(result["errors"]) == 0
    
    def test_validate_patch_invalid(self):
        """Test de validation d'un patch invalide."""
        manager = PatchManager()
        
        patch_text = "not a patch"
        
        result = manager.validate_patch(patch_text)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
    
    def test_get_patch_info(self):
        """Test d'analyse d'un patch."""
        manager = PatchManager()
        
        patch_text = """--- file.py
+++ file.py
@@ -1,2 +1,2 @@
-old line 1
-old line 2
+new line 1
+new line 2
"""
        
        info = manager.get_patch_info(patch_text)
        assert info["total_lines"] > 0
        assert info["added_lines"] == 2
        assert info["removed_lines"] == 2
        assert "file.py" in info["files_affected"]


class TestDeterministicController:
    """Tests pour le contrôleur déterministe."""
    
    def test_controller_initialization(self):
        """Test d'initialisation du contrôleur."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            assert controller.base_dir == temp_dir
            assert isinstance(controller.patch_manager, PatchManager)
            assert len(controller.evaluation_history) == 0
    
    def test_evaluate_patch_success(self):
        """Test d'évaluation d'un patch réussie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            # Patch simple
            patch_text = """--- test.py
+++ test.py
@@ -1,1 +1,1 @@
-print("hello")
+print("world")
"""
            
            with patch.object(controller.patch_manager, 'validate_patch') as mock_validate:
                with patch.object(controller, '_calculate_delta_metrics') as mock_delta:
                    mock_validate.return_value = {"valid": True}
                    mock_delta.return_value = {"delta_total": 0.1}
                    
                    with patch('controller.deterministic.evaluate_obligations') as mock_eval:
                        mock_eval.return_value = ObligationResults(
                            tests_ok=True, lint_ok=True, types_ok=True,
                            security_ok=True, complexity_ok=True, docstring_ok=True
                        )
                        
                        result = controller.evaluate_patch(patch_text)
                        
                        assert result["success"] == True
                        assert "obligation_results" in result
                        assert "delta_metrics" in result
    
    def test_evaluate_patch_failure(self):
        """Test d'évaluation d'un patch échouée."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            # Patch invalide
            patch_text = "invalid patch"
            
            with patch.object(controller.patch_manager, 'validate_patch') as mock_validate:
                mock_validate.return_value = {"valid": False, "errors": ["Invalid format"]}
                
                result = controller.evaluate_patch(patch_text)
                
                assert result["success"] == False
                assert "error" in result
    
    def test_batch_evaluate(self):
        """Test d'évaluation en lot."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            patches = [
                "patch1",
                "patch2",
                "patch3"
            ]
            
            with patch.object(controller, 'evaluate_patch') as mock_eval:
                mock_eval.side_effect = [
                    {"success": True, "violations": 0},
                    {"success": False, "violations": 2},
                    {"success": True, "violations": 1}
                ]
                
                results = controller.batch_evaluate(patches)
                
                assert len(results) == 3
                assert results[0]["success"] == True
                assert results[1]["success"] == False
                assert results[2]["success"] == True
    
    def test_get_best_patch(self):
        """Test de sélection du meilleur patch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            patches = ["patch1", "patch2", "patch3"]
            
            with patch.object(controller, 'batch_evaluate') as mock_batch:
                mock_batch.return_value = [
                    {"success": True, "violations": 2},
                    {"success": True, "violations": 0},
                    {"success": False, "violations": 5}
                ]
                
                best_index, best_result = controller.get_best_patch(patches)
                
                assert best_index == 1  # Le patch avec 0 violations
                assert best_result["success"] == True
                assert best_result["violations"] == 0
    
    def test_get_evaluation_stats(self):
        """Test des statistiques d'évaluation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            controller = DeterministicController(temp_dir)
            
            # Ajouter des évaluations à l'historique
            controller.evaluation_history = [
                {"success": True, "violations": 0, "delta_total": 0.1, "evaluation_time_ms": 1000},
                {"success": False, "violations": 2, "delta_total": 0.3, "evaluation_time_ms": 1500},
                {"success": True, "violations": 1, "delta_total": 0.2, "evaluation_time_ms": 1200}
            ]
            
            stats = controller.get_evaluation_stats()
            
            assert stats["total_evaluations"] == 3
            assert stats["successful_evaluations"] == 2
            assert stats["success_rate"] == 2/3
            assert stats["average_violations"] == 1.0
            assert stats["average_delta"] == 0.2
            assert stats["average_time_ms"] == 1233.33


if __name__ == "__main__":
    pytest.main([__file__])

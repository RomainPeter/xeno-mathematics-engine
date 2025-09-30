#!/usr/bin/env python3
"""
Tests for orchestrator LLM integration
"""
import pytest
import json
import tempfile
import os


class TestOrchestratorLLM:
    """Test orchestrator LLM functionality"""

    def test_orchestrator_import(self):
        """Test that orchestrator can be imported"""
        try:
            import importlib.util

            spec = importlib.util.find_spec("orchestrator.skeleton_llm")
            if spec:
                # Module exists, test passed
                assert True
            else:
                pytest.skip("Orchestrator LLM not available")
        except ImportError:
            pytest.skip("Orchestrator LLM not available")

    def test_orchestrator_mock(self):
        """Test orchestrator with mock data"""
        try:
            import importlib.util

            spec = importlib.util.find_spec("orchestrator.skeleton_llm")
            if spec:
                from orchestrator.skeleton_llm import Orchestrator

                # Create temporary plan and state files
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as plan_file:
                    plan = {"steps": [{"operator": "test", "params": {}}]}
                    json.dump(plan, plan_file)
                    plan_path = plan_file.name

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as state_file:
                    state = {
                        "H": ["goal:test"],
                        "E": [],
                        "K": ["tests_ok"],
                        "A": [],
                        "J": [],
                    }
                    json.dump(state, state_file)
                    state_path = state_file.name

                # Create orchestrator
                orchestrator = Orchestrator(plan_path, state_path)

                # Test loading
                orchestrator.load_data()
                assert orchestrator.plan is not None
                assert orchestrator.state is not None

                # Cleanup
                os.unlink(plan_path)
                os.unlink(state_path)
            else:
                pytest.skip("Orchestrator LLM not available")
        except ImportError:
            pytest.skip("Orchestrator LLM not available")

    def test_orchestrator_mock_llm(self):
        """Test orchestrator with mock LLM"""
        try:
            import importlib.util

            spec = importlib.util.find_spec("orchestrator.skeleton_llm")
            if spec:
                from orchestrator.skeleton_llm import Orchestrator
                from unittest.mock import MagicMock

                # Create mock LLM adapter
                mock_adapter = MagicMock()
                mock_adapter.ping.return_value = {"ok": True, "model": "mock"}
                mock_adapter.call_generalize.return_value = {
                    "response": {"action": {"name": "mock_action"}},
                    "meta": {"cache_hit": False},
                }
                mock_adapter.call_meet.return_value = {
                    "response": {"plan": ["mock_step"]},
                    "meta": {"cache_hit": False},
                }

                # Create temporary files
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as plan_file:
                    plan = {"steps": [{"operator": "test", "params": {}}]}
                    json.dump(plan, plan_file)
                    plan_path = plan_file.name

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as state_file:
                    state = {
                        "H": ["goal:test"],
                        "E": [],
                        "K": ["tests_ok"],
                        "A": [],
                        "J": [],
                    }
                    json.dump(state, state_file)
                    state_path = state_file.name

                # Test orchestrator with mock
                orchestrator = Orchestrator(plan_path, state_path, mock_adapter)
                orchestrator.load_data()

                # Test ping
                result = orchestrator.llm_adapter.ping()
                assert result["ok"] is True

                # Cleanup
                os.unlink(plan_path)
                os.unlink(state_path)
            else:
                pytest.skip("Orchestrator LLM not available")
        except ImportError:
            pytest.skip("Orchestrator LLM not available")


if __name__ == "__main__":
    pytest.main([__file__])

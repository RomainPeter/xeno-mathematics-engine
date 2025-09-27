#!/usr/bin/env python3
"""
Tests for Orchestrator LLM adapter
"""
import tempfile
from unittest.mock import patch, MagicMock


from orchestrator.adapter_llm import OrchestratorLLMAdapter, PromptContract


class TestOrchestratorLLM:
    """Test Orchestrator LLM adapter functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = OrchestratorLLMAdapter()

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_prompt_contract_meet(self):
        """Test Meet operator contract building"""
        contract = PromptContract.build_meet_contract(
            task="test task",
            inputs=[{"name": "x", "type": "object", "value": "{}"}],
            constraints=["JSON only"],
        )

        assert contract["role"] == "Meet"
        assert contract["task"] == "test task"
        assert (
            contract["output_schema_uri"]
            == "https://spec.proof.engine/v0.1/plan.schema.json"
        )
        assert contract["budgets"]["tokens"] == 400

    def test_prompt_contract_generalize(self):
        """Test Generalize operator contract building"""
        contract = PromptContract.build_generalize_contract(
            task="generate action",
            inputs=[{"name": "context", "type": "object", "value": "{}"}],
            constraints=["Valid JSON"],
        )

        assert contract["role"] == "Generalize"
        assert (
            contract["output_schema_uri"]
            == "https://spec.proof.engine/v0.1/pcap.schema.json"
        )
        assert contract["budgets"]["tokens"] == 600

    def test_prompt_contract_refute(self):
        """Test Refute operator contract building"""
        contract = PromptContract.build_refute_contract(
            task="analyze failure",
            inputs=[{"name": "evidence", "type": "object", "value": "{}"}],
            constraints=["Structured output"],
        )

        assert contract["role"] == "Refute"
        assert (
            contract["output_schema_uri"]
            == "https://spec.proof.engine/v0.1/failreason.schema.json"
        )
        assert contract["budgets"]["tokens"] == 300

    def test_contract_to_messages(self):
        """Test contract to messages conversion"""
        contract = {
            "role": "Meet",
            "task": "test task",
            "constraints": ["JSON only"],
            "output_schema_uri": "https://spec.proof.engine/v0.1/plan.schema.json",
        }

        messages = self.adapter._contract_to_messages(contract)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "test task" in messages[1]["content"]

    def test_response_validation(self):
        """Test response validation logic"""
        # Valid plan response
        valid_plan = '{"plan": ["step1", "step2"], "est_success": 0.8}'
        assert self.adapter._validate_response(valid_plan, "plan.schema.json") is True

        # Valid PCAP response
        valid_pcap = '{"action": {"name": "test"}, "operator": "generalize"}'
        assert self.adapter._validate_response(valid_pcap, "pcap.schema.json") is True

        # Valid FailReason response
        valid_fail = '{"reason": "test", "category": "error"}'
        assert (
            self.adapter._validate_response(valid_fail, "failreason.schema.json")
            is True
        )

        # Invalid JSON
        assert self.adapter._validate_response("not json", "plan.schema.json") is False

        # Missing required fields
        invalid_plan = '{"wrong": "field"}'
        assert (
            self.adapter._validate_response(invalid_plan, "plan.schema.json") is False
        )

    @patch("orchestrator.adapter_llm.OpenRouterAdapter")
    def test_call_meet_mock(self, mock_adapter_class):
        """Test Meet operator call with mocked adapter"""
        # Mock the adapter
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        # Mock response
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"plan": ["step1", "step2"], "est_success": 0.8}'
                    }
                }
            ]
        }
        mock_meta = {"cache_hit": False, "consistency_calls": 3}
        mock_adapter.call_llm.return_value = (mock_response, mock_meta)

        # Create adapter with mocked LLM
        adapter = OrchestratorLLMAdapter(mock_adapter)

        # Call Meet operator
        result = adapter.call_meet(
            task="test task",
            x_summary={"H": [], "E": []},
            obligations=["test_obligation"],
        )

        assert "response" in result
        assert "meta" in result
        assert "contract" in result
        assert result["response"]["plan"] == ["step1", "step2"]
        assert result["response"]["est_success"] == 0.8

    @patch("orchestrator.adapter_llm.OpenRouterAdapter")
    def test_call_generalize_mock(self, mock_adapter_class):
        """Test Generalize operator call with mocked adapter"""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"action": {"name": "test_action"}, "operator": "generalize"}'
                    }
                }
            ]
        }
        mock_meta = {"cache_hit": True, "consistency_calls": 0}
        mock_adapter.call_llm.return_value = (mock_response, mock_meta)

        adapter = OrchestratorLLMAdapter(mock_adapter)

        result = adapter.call_generalize(
            task="generate action",
            context={"test": "context"},
            constraints=["valid_json"],
        )

        assert result["response"]["action"]["name"] == "test_action"
        assert result["meta"]["cache_hit"] is True

    @patch("orchestrator.adapter_llm.OpenRouterAdapter")
    def test_call_refute_mock(self, mock_adapter_class):
        """Test Refute operator call with mocked adapter"""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": '{"reason": "validation_failed", "category": "syntax_error"}'
                    }
                }
            ]
        }
        mock_meta = {"cache_hit": False, "consistency_calls": 2}
        mock_adapter.call_llm.return_value = (mock_response, mock_meta)

        adapter = OrchestratorLLMAdapter(mock_adapter)

        result = adapter.call_refute(
            task="analyze failure",
            evidence={"error": "test"},
            constraints=["structured"],
        )

        assert result["response"]["reason"] == "validation_failed"
        assert result["response"]["category"] == "syntax_error"

    @patch("orchestrator.adapter_llm.OpenRouterAdapter")
    def test_fallback_on_invalid_response(self, mock_adapter_class):
        """Test fallback behavior on invalid LLM response"""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        # Mock invalid response
        mock_response = {"choices": [{"message": {"content": "invalid json response"}}]}
        mock_meta = {"cache_hit": False, "consistency_calls": 1}
        mock_adapter.call_llm.return_value = (mock_response, mock_meta)

        adapter = OrchestratorLLMAdapter(mock_adapter)

        # Call Meet with invalid response
        result = adapter.call_meet(
            task="test task", x_summary={"H": [], "E": []}, obligations=["test"]
        )

        # Should fallback to default response
        assert "plan" in result["response"]
        assert "fallback_step" in result["response"]["plan"]

    def test_ping(self):
        """Test ping functionality"""
        with patch.object(self.adapter.llm_adapter, "ping") as mock_ping:
            mock_ping.return_value = {"ok": True, "model": "test"}

            result = self.adapter.ping()
            assert result["ok"] is True
            assert result["model"] == "test"

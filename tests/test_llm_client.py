#!/usr/bin/env python3
"""
Tests for LLM Client v0.1 with auto-consistency
"""

import os
import tempfile
import time
from unittest.mock import MagicMock, patch

from proofengine.core.llm_client import LLMClient, LLMConfig


class TestLLMClient:
    """Test LLM Client functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = LLMConfig(
            api_key="test-key",
            cache_dir=os.path.join(self.temp_dir, "cache"),
            logs_dir=os.path.join(self.temp_dir, "logs"),
            n_consistency=2,  # Reduced for testing
            temperature=0.0,
        )
        self.client = LLMClient(self.config)

    def teardown_method(self):
        """Cleanup test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_defaults(self):
        """Test configuration defaults"""
        config = LLMConfig()
        assert config.model == "moonshotai/kimi-k2:free"
        assert config.temperature == 0.0
        assert config.top_p == 1.0
        assert config.max_tokens == 800
        assert config.n_consistency == 3

    def test_cache_key_generation(self):
        """Test cache key generation"""
        prompt = "test prompt"
        params = {"test": "value"}
        key1 = self.client._get_cache_key(prompt, params)
        key2 = self.client._get_cache_key(prompt, params)
        assert key1 == key2  # Deterministic

        # Different params should generate different keys
        params2 = {"test": "different"}
        key3 = self.client._get_cache_key(prompt, params2)
        assert key1 != key3

    def test_cache_operations(self):
        """Test cache save/load operations"""
        cache_key = "test_key"
        test_data = {"response": "test", "timestamp": time.time()}

        # Save to cache
        self.client._save_to_cache(cache_key, test_data)

        # Load from cache
        cached_data = self.client._get_from_cache(cache_key)
        assert cached_data == test_data

        # Non-existent key
        assert self.client._get_from_cache("non_existent") is None

    def test_response_scoring(self):
        """Test response scoring logic"""
        # Valid JSON response
        valid_response = '{"plan": ["step1", "step2"], "success": 0.8}'
        score1 = self.client._score_response(valid_response, "plan.schema.json")
        assert score1 > 0.5

        # Invalid JSON
        invalid_response = "not json"
        score2 = self.client._score_response(invalid_response, "plan.schema.json")
        assert score2 == 0.0

        # Empty response
        empty_response = "{}"
        score3 = self.client._score_response(empty_response, "plan.schema.json")
        assert score3 < score1

    def test_select_best_response(self):
        """Test best response selection"""
        responses = [
            {"choices": [{"message": {"content": '{"plan": ["good"], "success": 0.9}'}}]},
            {"choices": [{"message": {"content": '{"plan": ["bad"], "success": 0.1}'}}]},
            {"choices": [{"message": {"content": "invalid json"}}]},
        ]

        best = self.client._select_best_response(responses, "plan.schema.json")
        assert "good" in best["choices"][0]["message"]["content"]

    @patch("proofengine.core.llm_client.OpenAI")
    def test_mock_api_call(self, mock_openai):
        """Test API call with mocked client"""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"plan": ["test"], "success": 0.8}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {"total_tokens": 100}

        mock_client.chat.completions.create.return_value = mock_response

        # Create client with mocked OpenAI
        client = LLMClient(self.config)
        client.client = mock_client

        messages = [{"role": "user", "content": "test"}]
        response, meta = client.call_with_consistency(messages)

        assert "choices" in response
        assert meta["cache_hit"] is False
        assert meta["consistency_calls"] == 2  # n_consistency

    def test_offline_mode(self):
        """Test offline mode (no API key)"""
        config = LLMConfig(api_key="")
        client = LLMClient(config)

        # Should work in offline mode
        messages = [{"role": "user", "content": "test"}]
        response, meta = client.call_with_consistency(messages)

        assert "choices" in response
        assert meta["cache_hit"] is False

    def test_determinism(self):
        """Test deterministic behavior with temperature=0"""
        messages = [{"role": "user", "content": "test"}]

        # First call
        response1, meta1 = self.client.call_with_consistency(messages)

        # Second call should be cached
        response2, meta2 = self.client.call_with_consistency(messages)

        assert meta2["cache_hit"] is True
        assert response1 == response2

    def test_log_redaction(self):
        """Test log redaction functionality"""
        prompt = "Use API key sk-1234567890abcdef"
        redacted = self.client._redact_prompt(prompt)

        assert "sk-REDACTED-" in redacted
        assert "sk-1234567890abcdef" not in redacted

    def test_hmac_signing(self):
        """Test HMAC log signing"""
        prompt_hash = "abc123"
        resp_hash = "def456"

        signature1 = self.client._sign_log(prompt_hash, resp_hash)
        signature2 = self.client._sign_log(prompt_hash, resp_hash)

        assert signature1 == signature2  # Deterministic
        assert len(signature1) == 64  # SHA256 hex length

    def test_ping_offline(self):
        """Test ping in offline mode"""
        config = LLMConfig(api_key="")
        client = LLMClient(config)

        result = client.ping()
        assert result["ok"] is True
        assert result["model"] == "mock"

    @patch("proofengine.core.llm_client.OpenAI")
    def test_ping_online(self, mock_openai):
        """Test ping with real API"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "pong"
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {"total_tokens": 10}

        mock_client.chat.completions.create.return_value = mock_response

        client = LLMClient(self.config)
        client.client = mock_client

        result = client.ping()
        assert result["ok"] is True
        assert "latency_ms" in result

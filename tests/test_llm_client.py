"""
Tests pour le client LLM.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from proofengine.core.llm_client import LLMClient, LLMConfig


class TestLLMConfig:
    """Tests pour la configuration LLM."""

    def test_default_config(self):
        """Test de la configuration par défaut."""
        config = LLMConfig()
        assert config.model == "x-ai/grok-4-fast:free"
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.cache_dir == "out/llm_cache"

    def test_config_from_env(self):
        """Test de la configuration depuis les variables d'environnement."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_MODEL": "test-model",
                "OPENROUTER_API_KEY": "test-key",
                "HTTP_REFERER": "test-referer",
                "X_TITLE": "test-title",
            },
        ):
            config = LLMConfig()
            assert config.model == "test-model"
            assert config.api_key == "test-key"
            assert config.referer == "test-referer"
            assert config.title == "test-title"


class TestLLMClient:
    """Tests pour le client LLM."""

    def test_init_without_api_key(self):
        """Test d'initialisation sans clé API."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY missing"):
                LLMClient()

    def test_init_with_api_key(self):
        """Test d'initialisation avec clé API."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = LLMClient()
            assert client.cfg.api_key == "test-key"

    def test_cache_key_generation(self):
        """Test de génération des clés de cache."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = LLMClient()

            key1 = client._cache_key("system", "user", 42)
            key2 = client._cache_key("system", "user", 42)
            key3 = client._cache_key("system", "user", 43)

            assert key1 == key2
            assert key1 != key3

    @patch("core.llm_client.OpenAI")
    def test_generate_json_success(self, mock_openai):
        """Test de génération JSON réussie."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            # Mock de la réponse OpenAI
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"result": "success"}'
            mock_response.usage = MagicMock()
            mock_response.usage.model_dump.return_value = {"tokens": 100}

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = LLMClient()
            data, meta = client.generate_json("system", "user", seed=42)

            assert data == {"result": "success"}
            assert "latency_ms" in meta
            assert "model" in meta

    @patch("core.llm_client.OpenAI")
    def test_generate_json_error(self, mock_openai):
        """Test de génération JSON avec erreur."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            client = LLMClient()

            with pytest.raises(RuntimeError, match="LLM API error"):
                client.generate_json("system", "user")

    @patch("core.llm_client.OpenAI")
    def test_ping_success(self, mock_openai):
        """Test de ping réussi."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            # Mock de la réponse
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"ping": true}'
            mock_response.usage = MagicMock()
            mock_response.usage.model_dump.return_value = {"tokens": 10}

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = LLMClient()
            result = client.ping()

            assert result["status"] == "ok"
            assert "response" in result
            assert "meta" in result

    @patch("core.llm_client.OpenAI")
    def test_ping_error(self, mock_openai):
        """Test de ping avec erreur."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception(
                "Connection error"
            )
            mock_openai.return_value = mock_client

            client = LLMClient()
            result = client.ping()

            assert result["status"] == "error"
            assert "error" in result

    def test_clear_cache(self):
        """Test de nettoyage du cache."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = LLMClient()

            # Mock du répertoire de cache
            with patch("os.listdir", return_value=["file1.json", "file2.json"]):
                with patch("os.path.join", side_effect=lambda *args: "/".join(args)):
                    with patch("os.remove") as mock_remove:
                        count = client.clear_cache()

                        assert count == 2
                        assert mock_remove.call_count == 2

    def test_get_cache_stats(self):
        """Test des statistiques du cache."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = LLMClient()

            # Mock des statistiques du cache
            with patch("os.path.exists", return_value=True):
                with patch("os.listdir", return_value=["file1.json", "file2.json"]):
                    with patch("os.path.getsize", return_value=1024):
                        stats = client.get_cache_stats()

                        assert stats["count"] == 2
                        assert stats["size_bytes"] == 2048
                        assert "cache_dir" in stats


class TestLLMClientIntegration:
    """Tests d'intégration pour le client LLM."""

    @patch("core.llm_client.OpenAI")
    def test_full_workflow(self, mock_openai):
        """Test du workflow complet."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            # Mock de la réponse
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = '{"plan": ["step1", "step2"], "est_success": 0.8}'
            mock_response.usage = MagicMock()
            mock_response.usage.model_dump.return_value = {"tokens": 150}

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            client = LLMClient()

            # Test de génération
            data, meta = client.generate_json(
                "You are a planner",
                "Create a plan for task X",
                seed=42,
                temperature=0.7,
            )

            assert data["plan"] == ["step1", "step2"]
            assert data["est_success"] == 0.8
            assert meta["model"] == "x-ai/grok-4-fast:free"
            assert "latency_ms" in meta

            # Vérifier que l'API a été appelée avec les bons paramètres
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args

            assert call_args[1]["model"] == "x-ai/grok-4-fast:free"
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["seed"] == 42
            assert call_args[1]["response_format"]["type"] == "json_object"


if __name__ == "__main__":
    pytest.main([__file__])

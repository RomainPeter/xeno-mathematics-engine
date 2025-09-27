#!/usr/bin/env python3
"""
OpenRouter adapter for LLM calls
"""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..core.llm_client_v2 import LLMClient, LLMConfig


@dataclass
class OpenRouterConfig:
    """OpenRouter-specific configuration"""

    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "moonshotai/kimi-k2:free"
    http_referer: str = "https://github.com/romainpeter/proofengine"
    x_title: str = "ProofEngine Demo"

    def __post_init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", self.api_key)
        self.base_url = os.getenv("OPENROUTER_BASE_URL", self.base_url)
        self.model = os.getenv("OPENROUTER_MODEL", self.model)
        self.http_referer = os.getenv("HTTP_REFERER", self.http_referer)
        self.x_title = os.getenv("X_TITLE", self.x_title)


class OpenRouterAdapter:
    """OpenRouter API adapter with proper headers and error handling"""

    def __init__(self, config: Optional[OpenRouterConfig] = None):
        self.config = config or OpenRouterConfig()
        self.llm_config = LLMConfig(
            model=self.config.model,
            base_url=self.config.base_url,
            api_key=self.config.api_key,
        )
        self.client = LLMClient(self.llm_config)

    def get_headers(self) -> Dict[str, str]:
        """Get OpenRouter-specific headers"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "HTTP-Referer": self.config.http_referer,
            "X-Title": self.config.x_title,
            "Content-Type": "application/json",
        }

    def call_llm(
        self,
        messages: List[Dict[str, str]],
        params: Dict[str, Any] = None,
        expected_schema: str = None,
    ) -> Dict[str, Any]:
        """Call LLM through OpenRouter with proper headers"""
        if params is None:
            params = {}

        # Add OpenRouter-specific parameters
        params.update({"headers": self.get_headers()})

        return self.client.call_with_consistency(messages, params, expected_schema)

    def ping(self) -> Dict[str, Any]:
        """Test OpenRouter connectivity"""
        return self.client.ping()

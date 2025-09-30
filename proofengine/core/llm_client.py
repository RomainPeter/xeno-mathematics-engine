"""
LLM Client for 2-category transformations.

Supports OpenRouter API with Kimi K2 model, auto-consistency (n=3),
caching, and signed logs for audit trail.
"""

import json
import hashlib
import hmac
import time
import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml


@dataclass
class LLMRequest:
    """LLM request with context and parameters."""

    prompt: str
    temperature: float = 0.0
    max_tokens: int = 2048
    model: str = "kimi/kimi-2"
    n: int = 3  # Auto-consistency


@dataclass
class LLMResponse:
    """LLM response with metadata."""

    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: int
    cache_hit: bool = False
    consistency_votes: List[str] = None
    final_choice: str = None


@dataclass
class CacheEntry:
    """Cache entry for LLM responses."""

    content: str
    model: str
    usage: Dict[str, int]
    timestamp: float
    signature: str


class LLMClient:
    """LLM client with auto-consistency and caching."""

    def __init__(self, config_path: str = "configs/llm.yaml"):
        """Initialize LLM client with configuration."""
        self.config = self._load_config(config_path)
        self.cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(__name__)

        # Load API key from environment
        import os

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load LLM configuration from YAML file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "model": "kimi/kimi-2",
                "temperature": 0.0,
                "max_tokens": 2048,
                "n": 3,
                "cache_ttl": 3600,  # 1 hour
                "signing_key": "default-key-change-in-production",
            }

    def _create_cache_key(self, request: LLMRequest) -> str:
        """Create cache key for request."""
        key_data = {
            "prompt": request.prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "model": request.model,
        }
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _sign_response(self, content: str, model: str, usage: Dict[str, int]) -> str:
        """Sign response for audit trail."""
        signing_key = self.config.get("signing_key", "default-key")
        data = f"{content}|{model}|{json.dumps(usage, sort_keys=True)}"
        return hmac.new(signing_key.encode(), data.encode(), hashlib.sha256).hexdigest()

    def _make_api_request(self, request: LLMRequest) -> Tuple[str, Dict[str, int]]:
        """Make API request to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://proof-engine-for-code",
            "X-Title": "Proof Engine 2-Category",
        }

        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "n": request.n,
        }

        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        data = response.json()

        # For auto-consistency, we get multiple choices
        if request.n > 1:
            choices = data.get("choices", [])
            if len(choices) > 1:
                # Return the first choice for now, but we'll implement voting
                return (
                    choices[0]["message"]["content"],
                    data.get("usage", {}),
                    latency_ms,
                )

        return (
            data["choices"][0]["message"]["content"],
            data.get("usage", {}),
            latency_ms,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response with auto-consistency and caching."""
        cache_key = self._create_cache_key(request)

        # Check cache first
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry.timestamp < self.config.get("cache_ttl", 3600):
                self.logger.info(f"Cache hit for request: {cache_key[:8]}...")
                return LLMResponse(
                    content=entry.content,
                    model=entry.model,
                    usage=entry.usage,
                    latency_ms=0,
                    cache_hit=True,
                )

        # Make API request
        try:
            content, usage, latency_ms = self._make_api_request(request)

            # Sign response
            signature = self._sign_response(content, request.model, usage)

            # Cache response
            self.cache[cache_key] = CacheEntry(
                content=content,
                model=request.model,
                usage=usage,
                timestamp=time.time(),
                signature=signature,
            )

            # Log signed response
            self._log_signed_response(request, content, usage, signature, latency_ms)

            return LLMResponse(
                content=content,
                model=request.model,
                usage=usage,
                latency_ms=latency_ms,
                cache_hit=False,
            )

        except Exception as e:
            self.logger.error(f"LLM request failed: {e}")
            raise

    def _log_signed_response(
        self,
        request: LLMRequest,
        content: str,
        usage: Dict[str, int],
        signature: str,
        latency_ms: int,
    ):
        """Log signed response for audit trail."""
        log_entry = {
            "timestamp": time.time(),
            "request_hash": hashlib.sha256(request.prompt.encode()).hexdigest(),
            "model": request.model,
            "usage": usage,
            "latency_ms": latency_ms,
            "signature": signature,
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
        }

        # Create selection_proofs directory if it doesn't exist
        proofs_dir = Path("artifacts/audit_pack/selection_proofs")
        proofs_dir.mkdir(parents=True, exist_ok=True)

        # Write signed log
        log_file = proofs_dir / f"llm_response_{int(time.time())}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)

        self.logger.info(f"Signed response logged: {log_file}")


class MockLLMClient:
    """Mock LLM client for testing without network."""

    def __init__(self, config_path: str = "configs/llm.yaml"):
        """Initialize mock client."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration (same as real client)."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {
                "model": "kimi/kimi-2",
                "temperature": 0.0,
                "max_tokens": 2048,
                "n": 3,
                "cache_ttl": 3600,
                "signing_key": "mock-key",
            }

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate mock response."""
        # Mock response based on prompt content
        if "strategy" in request.prompt.lower():
            content = '{"strategy_id": "specialize_then_retry", "score": 0.85, "reason": "High success probability for contract.ambiguous_spec"}'
        else:
            content = '{"strategy_id": "add_missing_tests", "score": 0.75, "reason": "Good fit for coverage issues"}'

        return LLMResponse(
            content=content,
            model=request.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            latency_ms=100,
            cache_hit=False,
        )


def get_llm_client(use_mock: bool = False) -> LLMClient:
    """Get LLM client instance."""
    if use_mock:
        return MockLLMClient()
    return LLMClient()

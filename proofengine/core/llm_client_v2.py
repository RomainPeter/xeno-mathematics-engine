#!/usr/bin/env python3
"""
LLM Client v2 with auto-consistency and signed logs
"""
import hashlib
import json
import os
import time
import hmac
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()


@dataclass
class LLMConfig:
    model: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_MODEL", "moonshotai/kimi-k2:free").strip()
    )
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip()
    )
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "").strip())
    cache_dir: str = field(
        default_factory=lambda: os.getenv("LLM_CACHE_DIR", "proofengine/out/llm_cache").strip()
    )
    logs_dir: str = field(
        default_factory=lambda: os.getenv("LLM_LOGS_DIR", "proofengine/out/llm_logs").strip()
    )
    n_consistency: int = field(default_factory=lambda: int(os.getenv("LLM_N_CONSISTENCY", "3")))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.0")))
    top_p: float = field(default_factory=lambda: float(os.getenv("LLM_TOP_P", "1.0")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "800")))


class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.client = None
        self._init_client()
        self._ensure_dirs()

    def _init_client(self):
        """Initialize OpenAI client with OpenRouter config"""
        if not self.config.api_key:
            print("Warning: No OPENROUTER_API_KEY found, using mock client")
            self.client = None
            return

        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def _ensure_dirs(self):
        """Ensure cache and logs directories exist"""
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.logs_dir).mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate cache key from model, params, and prompt"""
        content = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.max_tokens,
            "prompt": prompt,
        }
        content.update(params)

        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get response from cache if available"""
        cache_file = Path(self.config.cache_dir) / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_to_cache(self, cache_key: str, response: Dict[str, Any]):
        """Save response to cache"""
        cache_file = Path(self.config.cache_dir) / f"{cache_key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

    def _log_request(
        self,
        prompt_hash: str,
        response_hash: str,
        prompt_redacted: str,
        usage: Dict[str, Any],
    ):
        """Log request with HMAC signature"""
        log_entry = {
            "ts": time.time(),
            "model": self.config.model,
            "prompt_hash": prompt_hash,
            "resp_hash": response_hash,
            "prompt_redacted": prompt_redacted,
            "usage": usage,
            "signature": self._sign_log(prompt_hash, response_hash),
        }

        # Save to daily log file
        log_file = Path(self.config.logs_dir) / f"{time.strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _sign_log(self, prompt_hash: str, response_hash: str) -> str:
        """Sign log entry with HMAC"""
        log_secret = os.getenv("LLM_LOG_SECRET", "default-secret-change-me")
        message = f"{prompt_hash}||{response_hash}"
        return hmac.new(log_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _redact_prompt(self, prompt: str) -> str:
        """Redact sensitive information from prompt"""
        # Simple redaction - replace potential secrets
        redacted = prompt
        redacted = redacted.replace("sk-", "sk-REDACTED-")
        redacted = redacted.replace("password", "p***word")
        redacted = redacted.replace("token", "t***en")
        return redacted

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
    )
    def _call_api(self, messages: List[Dict[str, str]], params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with retry logic"""
        if not self.client:
            # Mock response for testing
            return {
                "choices": [
                    {"message": {"content": '{"plan": ["mock_step"], "est_success": 0.8}'}}
                ],
                "usage": {
                    "total_tokens": 100,
                    "prompt_tokens": 50,
                    "completion_tokens": 50,
                },
            }

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
            **params,
        )

        return {
            "choices": [
                {"message": {"content": choice.message.content}} for choice in response.choices
            ],
            "usage": response.usage.model_dump() if response.usage else {},
        }

    def _score_response(self, response: str, expected_schema: str) -> float:
        """Score response based on validity and quality"""
        try:
            data = json.loads(response)

            # Basic validity checks
            if not isinstance(data, dict):
                return 0.0

            # Length penalty (prefer concise responses)
            length_penalty = min(len(response) / 1000, 1.0)

            # Schema compliance (basic check)
            schema_score = 1.0 if "plan" in data or "success" in data else 0.5

            return schema_score - (length_penalty * 0.1)

        except json.JSONDecodeError:
            return 0.0

    def _select_best_response(
        self, responses: List[Dict[str, Any]], expected_schema: str
    ) -> Dict[str, Any]:
        """Select best response from auto-consistency results"""
        if not responses:
            return {}

        if len(responses) == 1:
            return responses[0]

        # Score all responses
        scored_responses = []
        for resp in responses:
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            score = self._score_response(content, expected_schema)
            scored_responses.append((score, resp))

        # Sort by score (descending)
        scored_responses.sort(key=lambda x: x[0], reverse=True)

        # Return best response
        return scored_responses[0][1]

    def call_with_consistency(
        self,
        messages: List[Dict[str, str]],
        params: Dict[str, Any] = None,
        expected_schema: str = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Call LLM with auto-consistency (n=3) and return best response"""
        if params is None:
            params = {}

        # Check cache first
        prompt_str = json.dumps(messages, sort_keys=True)
        cache_key = self._get_cache_key(prompt_str, params)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached, {"cache_hit": True, "consistency_calls": 0}

        # Make multiple calls for consistency
        responses = []
        for i in range(self.config.n_consistency):
            try:
                response = self._call_api(messages, params)
                responses.append(response)
            except Exception as e:
                print(f"Consistency call {i+1} failed: {e}")
                continue

        if not responses:
            raise Exception("All consistency calls failed")

        # Select best response
        best_response = self._select_best_response(responses, expected_schema or "")

        # Cache the result
        cache_data = {
            "response": best_response,
            "consistency_calls": len(responses),
            "timestamp": time.time(),
        }
        self._save_to_cache(cache_key, cache_data)

        # Log the request
        prompt_hash = hashlib.sha256(prompt_str.encode()).hexdigest()
        resp_str = json.dumps(best_response, sort_keys=True)
        resp_hash = hashlib.sha256(resp_str.encode()).hexdigest()

        usage = best_response.get("usage", {})
        self._log_request(prompt_hash, resp_hash, self._redact_prompt(prompt_str), usage)

        return best_response, {
            "cache_hit": False,
            "consistency_calls": len(responses),
            "prompt_hash": prompt_hash,
            "resp_hash": resp_hash,
        }

    def ping(self) -> Dict[str, Any]:
        """Test LLM connectivity"""
        if not self.client:
            return {"ok": True, "model": "mock", "latency_ms": 0}

        start_time = time.time()
        try:
            response = self._call_api([{"role": "user", "content": "ping"}], {"max_tokens": 10})
            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "ok": True,
                "model": self.config.model,
                "latency_ms": latency_ms,
                "response": response,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


# Backward compatibility
LLMClientV1 = LLMClient

import hashlib
import json
import os
import pathlib
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

load_dotenv()


@dataclass
class LLMConfig:
    model: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_MODEL", "x-ai/grok-4-fast:free"
        ).strip()
    )
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
    )
    api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "").strip()
    )
    referer: str = field(
        default_factory=lambda: os.getenv("HTTP_REFERER", "https://example.com")
    )
    title: str = field(default_factory=lambda: os.getenv("X_TITLE", "ProofEngine Demo"))
    timeout: float = field(
        default_factory=lambda: float(os.getenv("OPENROUTER_TIMEOUT_SECS", "60"))
    )
    cache_dir: str = field(
        default_factory=lambda: os.getenv("PROOFENGINE_LLM_CACHE", "out/llm_cache")
    )


class LLMClient:
    """Lightweight wrapper around the OpenRouter Chat Completions API."""

    def __init__(self, cfg: Optional[LLMConfig] = None, use_cache: bool = True):
        self.cfg = cfg or LLMConfig()
        self.use_cache = use_cache
        self.cache_dir = pathlib.Path(self.cfg.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline = os.getenv("PROOFENGINE_OFFLINE", "0") == "1"

        if not self.cfg.api_key and not self.offline:
            raise RuntimeError("OPENROUTER_API_KEY missing")

        self.client = (
            None
            if self.offline
            else OpenAI(
                base_url=self.cfg.base_url,
                api_key=self.cfg.api_key,
                default_headers={
                    "HTTP-Referer": self.cfg.referer,
                    "X-Title": self.cfg.title,
                },
                timeout=self.cfg.timeout,
            )
        )

    def _cache_key(self, system: str, user: str, seed: Optional[int]) -> str:
        key_payload = json.dumps(
            {
                "model": self.cfg.model,
                "system": system,
                "user": user,
                "seed": seed,
            },
            sort_keys=True,
        )
        return hashlib.sha256(key_payload.encode("utf-8")).hexdigest()

    def _cache_path(self, cache_key: str) -> pathlib.Path:
        return self.cache_dir / f"{cache_key}.json"

    def _cache_get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        path = self._cache_path(cache_key)
        if self.use_cache and path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return None

    def _cache_set(self, cache_key: str, payload: Dict[str, Any]) -> None:
        if self.use_cache:
            with self._cache_path(cache_key).open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter(0.5, 2.0))
    def generate_json(
        self,
        system: str,
        user: str,
        seed: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        diversity = (
            f"DVAL::{random.randint(0, 10**9)}" if seed is None else f"SEED::{seed}"
        )
        user_payload = f"{user}\n\n{diversity}"
        cache_key = self._cache_key(system, user_payload, seed)

        cached = self._cache_get(cache_key)
        if cached:
            meta = cached.get("meta", {})
            meta["cache_hit"] = True
            return cached.get("data", {}), meta

        if self.offline or self.client is None:
            raise RuntimeError("Offline/cache-only mode and cache miss for prompt")

        start = time.time()
        response = self.client.chat.completions.create(
            model=self.cfg.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_payload},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            seed=seed,
        )
        latency_ms = int((time.time() - start) * 1000)

        content = response.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            data = (
                json.loads(content[start_idx : end_idx + 1])
                if start_idx != -1 and end_idx != -1
                else {}
            )

        usage = getattr(response, "usage", None)
        meta = {
            "model": self.cfg.model,
            "latency_ms": latency_ms,
            "usage": usage.model_dump() if usage else {},
            "cache_hit": False,
            "cache_key": cache_key,
        }

        self._cache_set(cache_key, {"data": data, "meta": meta})
        return data, meta

    def clear_cache(self) -> int:
        removed = 0
        if self.cache_dir.exists():
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    os.remove(self.cache_dir / filename)
                    removed += 1
        return removed

    def get_cache_stats(self) -> Dict[str, Any]:
        if not self.cache_dir.exists():
            return {"count": 0, "size_bytes": 0, "cache_dir": str(self.cache_dir)}

        count = 0
        size = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                count += 1
                size += os.path.getsize(self.cache_dir / filename)
        return {"count": count, "size_bytes": size, "cache_dir": self.cfg.cache_dir}

    def ping(self) -> Dict[str, Any]:
        try:
            data, meta = self.generate_json(
                'Respond with JSON {"ok": true, "model": "..."}',
                "Confirm availability",
                seed=1,
                temperature=0.0,
                max_tokens=32,
            )
            return {"status": "ok", "response": data, "meta": meta}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

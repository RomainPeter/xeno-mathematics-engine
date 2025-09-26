import os, time, json, hashlib, random, pathlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from dotenv import load_dotenv

load_dotenv()

# Add offline mode support
OFFLINE = os.getenv("PROOFENGINE_OFFLINE", "0") == "1"

CACHE_DIR = pathlib.Path("proofengine/out/llm_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class LLMConfig:
    model: str = os.getenv("OPENROUTER_MODEL", "").strip()
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    referer: str = os.getenv("HTTP_REFERER", "https://example.com")
    title: str = os.getenv("X_TITLE", "ProofEngine Demo")
    timeout: float = float(os.getenv("OPENROUTER_TIMEOUT_SECS", "60"))

class LLMError(RuntimeError): ...

class LLMClient:
    def __init__(self, cfg: Optional[LLMConfig] = None, use_cache: bool = True):
        self.cfg = cfg or LLMConfig()
        self.use_cache = use_cache
        self.offline = OFFLINE
        
        if not self.cfg.model:
            raise LLMError("OPENROUTER_MODEL missing")
        
        if self.offline and not self.cfg.api_key:
            self.client = None  # cache-only mode
        else:
            if not self.cfg.api_key:
                raise LLMError("OPENROUTER_API_KEY missing (set PROOFENGINE_OFFLINE=1 for cache-only)")
            self.client = OpenAI(
                base_url=self.cfg.base_url,
                api_key=self.cfg.api_key,
                default_headers={"HTTP-Referer": self.cfg.referer, "X-Title": self.cfg.title},
                timeout=self.cfg.timeout,
            )

    @staticmethod
    def _prompt_hash(model: str, system: str, user: str, seed: Optional[int]) -> str:
        m = hashlib.sha256()
        m.update((model + "\n" + system + "\n" + user + "\n" + str(seed)).encode("utf-8"))
        return m.hexdigest()

    def _cache_path(self, h: str) -> pathlib.Path:
        return CACHE_DIR / f"{h}.json"

    def _cache_get(self, h: str) -> Optional[Dict[str, Any]]:
        p = self._cache_path(h)
        if self.use_cache and p.exists():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _cache_set(self, h: str, payload: Dict[str, Any]) -> None:
        if self.use_cache:
            with self._cache_path(h).open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

    @retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter(0.5, 2.0))
    def generate_json(self, system: str, user: str, seed: Optional[int] = None,
                      temperature: float = 0.7, max_tokens: int = 1000) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        diversity = f"DVAL::{random.randint(0, 10**9)}" if seed is None else f"SEED::{seed}"
        user_payload = f"{user}\n\n{diversity}"
        h = self._prompt_hash(self.cfg.model, system, user_payload, seed)
        cached = self._cache_get(h)
        if cached is not None:
            meta = cached.get("_meta", {})
            meta["cache_hit"] = True
            return cached["data"], meta
        
        if self.offline or self.client is None:
            raise LLMError("Offline/cache-only mode and cache miss for prompt hash: " + h)
        
        t0 = time.time()
        resp = self.client.chat.completions.create(
            model=self.cfg.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user_payload}],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            seed=seed,
        )
        latency_ms = int((time.time() - t0) * 1000)
        content = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except Exception:
            start = content.find("{"); end = content.rfind("}")
            data = json.loads(content[start:end+1]) if start != -1 and end != -1 else {}
        usage = getattr(resp, "usage", None)
        meta = {"model": self.cfg.model, "latency_ms": latency_ms, "usage": usage.model_dump() if usage else {}, "prompt_hash": h, "cache_hit": False}
        self._cache_set(h, {"data": data, "_meta": meta})
        return data, meta

    def ping(self) -> Dict[str, Any]:
        sys = 'You output ONLY valid JSON: {"ok": true, "model": "..."}'
        usr = "Return ok=true and a short model name."
        data, meta = self.generate_json(sys, usr, seed=1, temperature=0.0, max_tokens=30)
        return {"data": data, "meta": meta}

"""
Client LLM pour OpenRouter avec cache local, retries et JSON strict.
"""

import os
import time
import json
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


@dataclass
class LLMConfig:
    """Configuration du client LLM."""
    model: str = os.getenv("OPENROUTER_MODEL", "x-ai/grok-2-fast")
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    referer: str = os.getenv("HTTP_REFERER", "https://example.com")
    title: str = os.getenv("X_TITLE", "ProofEngine Demo")
    timeout: float = 60.0
    cache_dir: str = "out/llm_cache"


class LLMClient:
    """Client LLM avec cache et retry."""
    
    def __init__(self, cfg: Optional[LLMConfig] = None):
        """Initialise le client LLM."""
        self.cfg = cfg or LLMConfig()
        if not self.cfg.api_key:
            raise RuntimeError("OPENROUTER_API_KEY missing")
        os.makedirs(self.cfg.cache_dir, exist_ok=True)
        
        self.client = OpenAI(
            base_url=self.cfg.base_url,
            api_key=self.cfg.api_key,
            default_headers={
                "HTTP-Referer": self.cfg.referer,
                "X-Title": self.cfg.title
            }
        )
    
    def _cache_key(self, sys: str, usr: str, seed: Optional[int]) -> str:
        """Génère une clé de cache basée sur le contenu."""
        h = hashlib.sha256((self.cfg.model + sys + usr + str(seed)).encode()).hexdigest()
        return os.path.join(self.cfg.cache_dir, h + ".json")
    
    @retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter(0.5, 2.0))
    def generate_json(self, system: str, user: str, seed: Optional[int] = None,
                      temperature: float = 0.7, max_tokens: int = 1200, 
                      use_cache: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Génère une réponse JSON du LLM avec cache et retry.
        
        Args:
            system: Prompt système
            user: Prompt utilisateur
            seed: Graine pour la reproductibilité
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens
            use_cache: Utiliser le cache si disponible
            
        Returns:
            Tuple[content, meta]: Contenu JSON et métadonnées
        """
        ck = self._cache_key(system, user, seed)
        
        # Vérifier le cache
        if use_cache and os.path.exists(ck):
            with open(ck) as f:
                data = json.load(f)
            return data["content"], data["meta"]
        
        # Appel au LLM
        t0 = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=self.cfg.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                seed=seed
            )
        except Exception as e:
            raise RuntimeError(f"LLM API error: {str(e)}")
        
        latency_ms = int((time.time() - t0) * 1000)
        content = resp.choices[0].message.content or "{}"
        
        # Parser le JSON
        try:
            data = json.loads(content) if content.strip().startswith("{") else {}
        except json.JSONDecodeError:
            data = {}
        
        # Métadonnées
        usage = getattr(resp, "usage", None)
        meta = {
            "model": self.cfg.model,
            "latency_ms": latency_ms,
            "usage": usage.model_dump() if usage else {},
            "temperature": temperature,
            "max_tokens": max_tokens,
            "seed": seed
        }
        
        # Sauvegarder en cache
        cache_data = {"content": data, "meta": meta}
        with open(ck, "w") as f:
            json.dump(cache_data, f, indent=2)
        
        return data, meta
    
    def ping(self) -> Dict[str, Any]:
        """Test de connectivité du LLM."""
        try:
            data, meta = self.generate_json(
                "You are a JSON API. Respond with a simple JSON object.",
                '{"ping": true}',
                seed=1,
                temperature=0.1,
                max_tokens=50
            )
            return {"status": "ok", "response": data, "meta": meta}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def clear_cache(self) -> int:
        """Vide le cache et retourne le nombre de fichiers supprimés."""
        if not os.path.exists(self.cfg.cache_dir):
            return 0
        
        count = 0
        for filename in os.listdir(self.cfg.cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(self.cfg.cache_dir, filename))
                count += 1
        
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        if not os.path.exists(self.cfg.cache_dir):
            return {"count": 0, "size_bytes": 0}
        
        count = 0
        size_bytes = 0
        
        for filename in os.listdir(self.cfg.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cfg.cache_dir, filename)
                count += 1
                size_bytes += os.path.getsize(filepath)
        
        return {
            "count": count,
            "size_bytes": size_bytes,
            "cache_dir": self.cfg.cache_dir
        }

from typing import Any, Dict, List, Optional
from proofengine.core.llm_client import LLMClient
from .prompts import GENERATOR_SYSTEM, GENERATOR_USER_TMPL


def propose_actions(
    task: str,
    context: str,
    obligations: str,
    k: int = 3,
    temperature: float = 0.8,
    client: Optional[LLMClient] = None,
) -> List[Dict[str, Any]]:
    llm = client or LLMClient()
    variants: List[Dict[str, Any]] = []
    for i in range(k):
        seed = 1000 + i
        user = GENERATOR_USER_TMPL.format(task=task, context=context, obligations=obligations)
        data, meta = llm.generate_json(GENERATOR_SYSTEM, user, seed=seed, temperature=temperature)
        if isinstance(data, dict) and "patch_unified" in data:
            variants.append({"proposal": data, "llm_meta": meta})
    return variants

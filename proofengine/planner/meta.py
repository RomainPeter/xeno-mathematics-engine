from typing import Any, Dict, Optional

from proofengine.core.llm_client import LLMClient

from .prompts import PLANNER_SYSTEM, PLANNER_USER_TMPL


def propose_plan(
    goal: str,
    x_summary: str,
    obligations: str,
    history_json: str,
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    llm = client or LLMClient()
    user = PLANNER_USER_TMPL.format(
        goal=goal, x_summary=x_summary, obligations=obligations, history=history_json
    )
    data, meta = llm.generate_json(PLANNER_SYSTEM, user, seed=42, temperature=0.2, max_tokens=600)
    plan = data.get("plan", []) if isinstance(data.get("plan", []), list) else []
    return {
        "plan": plan[:5],
        "est_success": data.get("est_success", 0.5),
        "est_cost": data.get("est_cost", 1.0),
        "notes": data.get("notes", ""),
        "llm_meta": meta,
    }

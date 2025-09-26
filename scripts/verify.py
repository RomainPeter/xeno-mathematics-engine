import os, json
from dotenv import load_dotenv

def jprint(obj): 
    print(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

def main():
    load_dotenv()
    ok = True
    # Check env
    env = {
        "OPENROUTER_API_KEY": "***" if os.getenv("OPENROUTER_API_KEY") else None,
        "OPENROUTER_MODEL": os.getenv("OPENROUTER_MODEL"),
        "HTTP_REFERER": os.getenv("HTTP_REFERER"),
        "X_TITLE": os.getenv("X_TITLE"),
    }
    if not os.getenv("OPENROUTER_API_KEY"):
        ok = False
        jprint({"ok": False, "reason": "missing OPENROUTER_API_KEY", "env": env})
        return
    try:
        from proofengine.core.llm_client import LLMClient
        from proofengine.planner.meta import propose_plan
        from proofengine.generator.stochastic import propose_actions
        client = LLMClient()
        ping = client.ping()
        plan = propose_plan("Improve sanitize_input", "{}", '["tests_ok","docstring_ok"]', "[]")
        actions = propose_actions("Sanitize input in utils.py", "toy repo", '["no eval","docstring_ok"]', k=2)
        jprint({"ok": True, "ping": ping["data"], "plan_len": len(plan["plan"]), "actions": len(actions)})
    except Exception as e:
        ok = False
        jprint({"ok": False, "error": str(e)})
    return ok

if __name__ == "__main__":
    main()
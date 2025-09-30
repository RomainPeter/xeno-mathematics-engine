#!/usr/bin/env python3
"""
Simple verification script for CI
"""
import os
import json
from dotenv import load_dotenv


def main():
    """Simple verification that doesn't require LLM"""
    load_dotenv()

    # Check if we have required files
    required_files = [
        "requirements.lock",
        "scripts/test_roundtrip.py",
        "orchestrator/skeleton.py",
        "plans/plan-hello.json",
        "state/x-hello.json",
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(json.dumps({"ok": False, "reason": "missing_files", "missing": missing_files}))
        return False

    # Check if we can import required modules
    try:
        import importlib.util

        # Test if modules exist
        llm_spec = importlib.util.find_spec("proofengine.core.llm_client")
        orchestrator_spec = importlib.util.find_spec("orchestrator.skeleton")

        if llm_spec and orchestrator_spec:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "reason": "all_checks_passed",
                        "files_checked": len(required_files),
                    }
                )
            )
            return True
        else:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "modules_not_found",
                        "llm_module": llm_spec is not None,
                        "orchestrator_module": orchestrator_spec is not None,
                    }
                )
            )
            return False
    except Exception as e:
        print(json.dumps({"ok": False, "reason": "import_error", "error": str(e)}))
        return False


if __name__ == "__main__":
    main()

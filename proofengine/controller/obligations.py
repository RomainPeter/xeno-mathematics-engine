import subprocess, json, os, shutil
from typing import Dict, Tuple

def run(cmd: list[str], cwd: str) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def ensure_tools():
    # install test deps if missing (best effort)
    if shutil.which("pytest") is None:
        try: 
            subprocess.run(["python", "-m", "pip", "install", "pytest", "flake8", "mypy", "bandit", "radon"], check=False)
        except Exception: 
            pass

def check_tests(cwd): 
    return run(["pytest", "-q"], cwd)[0] == 0

def check_flake8(cwd): 
    return run(["flake8", "."], cwd)[0] == 0

def check_mypy(cwd): 
    return run(["mypy", "."], cwd)[0] == 0

def check_bandit(cwd): 
    return run(["bandit", "-q", "-r", "."], cwd)[0] == 0

def check_complexity(cwd, max_cc=10):
    code, out, _ = run(["radon", "cc", "-s", "-j", "."], cwd)
    if code != 0: 
        return False
    try:
        data = json.loads(out or "{}")
    except Exception:
        return False
    for _file, funcs in data.items():
        for f in funcs:
            if f.get("complexity", 0) > max_cc:
                return False
    return True

def check_docstrings(cwd):
    ok = True
    for root, _, files in os.walk(cwd):
        for fn in files:
            if fn.endswith(".py") and not fn.startswith("_"):
                with open(os.path.join(root, fn), "r", encoding="utf-8") as f:
                    content = f.read().lstrip()
                    if not content.startswith('"""') and not content.startswith("'''"):
                        ok = False
    return ok

def evaluate_all(cwd: str) -> Dict[str, bool]:
    return {
        "tests_ok": check_tests(cwd),
        "lint_ok": check_flake8(cwd),
        "types_ok": check_mypy(cwd),
        "security_ok": check_bandit(cwd),
        "complexity_ok": check_complexity(cwd),
        "docstring_ok": check_docstrings(cwd),
    }

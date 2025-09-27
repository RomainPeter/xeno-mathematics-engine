PY=python3

.PHONY: setup verify demo audit-pack logs release schema-test validate fmt demo-s1 deps-lock

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
	@echo "Copy .env.example to .env and set OPENROUTER_* vars."

deps-lock:
	pip install pip-tools
	pip-compile requirements.in
	@echo "Dependencies locked in requirements.txt"

verify:
	. .venv/bin/activate && $(PY) scripts/verify.py

demo:
	. .venv/bin/activate && $(PY) scripts/demo.py

audit-pack:
	. .venv/bin/activate && $(PY) scripts/audit_pack.py

logs:
	. .venv/bin/activate && $(PY) scripts/make_logs.py

release: audit-pack logs
	. .venv/bin/activate && $(PY) scripts/make_release.py

validate:
	$(PY) scripts/test_roundtrip.py

fmt:
	black . && ruff check --fix .

demo-s1:
	. .venv/bin/activate && $(PY) orchestrator/skeleton.py --plan plans/plan-hello.json --state state/x-hello.json

demo-s1-llm:
	. .venv/bin/activate && $(PY) orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --llm kimi

demo-s1-mock:
	. .venv/bin/activate && $(PY) orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --llm mock

ci-local: verify demo audit-pack
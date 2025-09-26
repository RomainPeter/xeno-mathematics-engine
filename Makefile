PY=python3

.PHONY: setup verify demo audit-pack logs release

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
	@echo "Copy .env.example to .env and set OPENROUTER_* vars."

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
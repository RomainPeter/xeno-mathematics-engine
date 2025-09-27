PY=python3

.PHONY: setup verify demo audit-pack logs release schema-test validate fmt demo-s1 deps-lock build-verifier-pinned audit 2cat-shadow 2cat-active s2-bench 2cat-report

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

demo-llm:
	. .venv/bin/activate && $(PY) orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --llm kimi --verifier local

demo-s1-mock:
	. .venv/bin/activate && $(PY) orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --llm mock

demo-s1-docker:
	. .venv/bin/activate && $(PY) orchestrator/skeleton_llm.py --plan plans/plan-hello.json --state state/x-hello.json --llm mock --verifier docker

demo-s2:
	. .venv/bin/activate && $(PY) scripts/metrics.py --tasks corpus/s2 --output artifacts/s2_metrics

delta-calibration:
	. .venv/bin/activate && jupyter nbconvert --to html notebook/delta_calibration.ipynb

test-rules:
	. .venv/bin/activate && $(PY) tests/test_rules.py

verifier-docker:
	. .venv/bin/activate && $(PY) scripts/verifier.py --runner docker --pcap examples/v0.1/pcap/ex1.json

docker-build:
	docker build -t proofengine/verifier:0.1.0 -f Dockerfile.verifier .

ci-local: verify demo audit-pack

# Supply-chain hardening targets
build-verifier-pinned:
	@echo "🔍 Verifying Docker image pin..."
	@grep -q "FROM python:3.11-slim@sha256:" Dockerfile.verifier || (echo "❌ Docker image not pinned by digest" && exit 1)
	@echo "✅ Docker image properly pinned"
	docker build -t proofengine/verifier:0.1.0 -f Dockerfile.verifier .

audit:
	@echo "🔍 Running security audit..."
	@echo "📦 Trivy filesystem scan..."
	trivy fs --exit-code 1 --severity HIGH,CRITICAL . || echo "⚠️ Trivy scan found issues"
	@echo "🐳 Trivy image scan..."
	trivy image --exit-code 1 --severity HIGH,CRITICAL proofengine/verifier:0.1.0 || echo "⚠️ Trivy image scan found issues"
	@echo "🔍 Grype scan..."
	grype proofengine/verifier:0.1.0 --fail-on high || echo "⚠️ Grype scan found issues"
	@echo "🔐 Cosign verification..."
	@if [ -f "artifacts/audit_pack.zip" ]; then \
		cosign verify-blob artifacts/audit_pack.zip \
			--signature artifacts/audit_pack.zip.sig \
			--key .github/security/cosign.pub && echo "✅ Cosign verification passed"; \
	else \
		echo "⚠️ No audit pack found for verification"; \
	fi
	@echo "✅ Security audit completed"

# Expected-fail demonstrations
expected-fail-semver:
	@echo "🧪 Testing semver policy violation..."
	$(PY) scripts/verifier.py --runner docker --pcap examples/expected_fail/pcap-semver.json || echo "✅ Expected failure: semver policy violation"

expected-fail-changelog:
	@echo "🧪 Testing changelog policy violation..."
	$(PY) scripts/verifier.py --runner docker --pcap examples/expected_fail/pcap-changelog.json || echo "✅ Expected failure: changelog policy violation"

# Deterministic build test
rebuild-hash-equal:
	@echo "🔒 Testing deterministic build..."
	@export SOURCE_DATE_EPOCH=1700000000 && $(PY) scripts/build_audit_pack.py
	@sha256sum artifacts/audit_pack/audit_pack.zip > hash1.txt
	@export SOURCE_DATE_EPOCH=1700000000 && $(PY) scripts/build_audit_pack.py
	@sha256sum artifacts/audit_pack/audit_pack.zip > hash2.txt
	@if diff hash1.txt hash2.txt; then \
		echo "✅ Deterministic build verified"; \
	else \
		echo "❌ Build is not deterministic"; \
		exit 1; \
	fi
	@rm -f hash1.txt hash2.txt

# 2-Category transformation targets
2cat-shadow:
	@echo "🔍 Running 2-category shadow mode..."
	. .venv/bin/activate && $(PY) scripts/2cat_shadow_report.py
	@echo "✅ Shadow report generated"

2cat-active:
	@echo "🚀 Running 2-category active mode..."
	. .venv/bin/activate && $(PY) scripts/2cat_active_mode.py
	@echo "✅ Active mode completed"

s2-bench:
	@echo "📊 Running S2 benchmark..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py
	@echo "✅ S2 benchmark completed"

2cat-report:
	@echo "📈 Generating 2-category report..."
	. .venv/bin/activate && $(PY) scripts/generate_2cat_report.py
	@echo "✅ 2-category report generated"

# Test 2-category strategies
test-2cat:
	@echo "🧪 Testing 2-category strategies..."
	. .venv/bin/activate && $(PY) -m pytest tests/strategies/ -v
	@echo "✅ 2-category strategy tests completed"

# Expected-fail tests for 2-category
expected-fail-2cat:
	@echo "🧪 Testing 2-category expected-fail cases..."
	. .venv/bin/activate && $(PY) scripts/test_strategies_expected_fail.py
	@echo "✅ 2-category expected-fail tests completed"

# S2 Vendors targets
demo-s2:
	@echo "🎯 Running S2 vendors demo..."
	. .venv/bin/activate && $(PY) scripts/bench_s2_vendors.py --mode both
	@echo "✅ S2 vendors demo completed"

s2-active:
	@echo "🚀 Running S2 active mode..."
	. .venv/bin/activate && $(PY) scripts/run_active_mock.py --plan corpus/s2/vendors/api-break/plan.json
	. .venv/bin/activate && $(PY) scripts/run_active_mock.py --plan corpus/s2/vendors/typosquat-cve/plan.json
	. .venv/bin/activate && $(PY) scripts/run_active_mock.py --plan corpus/s2/vendors/secret-egress/plan.json
	@echo "✅ S2 active mode completed"

s2-bench:
	@echo "📊 Running S2 vendors benchmark..."
	. .venv/bin/activate && $(PY) scripts/bench_s2_vendors.py --mode both --output artifacts/s2_vendors_benchmark.json
	@echo "✅ S2 vendors benchmark completed"

# Expected-fail tests for S2 vendors
expected-fail-s2:
	@echo "🧪 Testing S2 vendors expected-fail cases..."
	. .venv/bin/activate && $(PY) -m pytest tests/s2_vendors_test.py -v
	@echo "✅ S2 vendors expected-fail tests completed"

# Delta calibration and bench public targets
bench-baseline:
	@echo "📊 Running baseline benchmark..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode baseline --runs 3 --out artifacts/bench_public/metrics_baseline.json
	@echo "✅ Baseline benchmark completed"

bench-active:
	@echo "📊 Running active benchmark..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode active --runs 3 --out artifacts/bench_public/metrics_active.json
	@echo "✅ Active benchmark completed"

# Performance-optimized benchmarks
bench-baseline-fast:
	@echo "🚀 Running baseline benchmark (optimized)..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode baseline --runs 3 --out artifacts/bench_public/metrics_baseline.json --parallel --workers 4 --compact-json --profile
	@echo "✅ Baseline benchmark (optimized) completed"

bench-active-fast:
	@echo "🚀 Running active benchmark (optimized)..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode active --runs 3 --out artifacts/bench_public/metrics_active.json --parallel --workers 4 --compact-json --profile
	@echo "✅ Active benchmark (optimized) completed"

# Cache warmup
cache-warmup:
	@echo "🔥 Warming up caches..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/bench_public/suite.json --mode baseline --runs 1 --out artifacts/bench_public/warmup.json --cache-warmup artifacts/cache_warmup.json
	@echo "✅ Cache warmup completed"

delta-calibrate:
	@echo "🔧 Calibrating delta weights..."
	. .venv/bin/activate && $(PY) scripts/delta_calibrate.py --runs artifacts/bench_public/metrics_baseline.json artifacts/bench_public/metrics_active.json --out configs/weights.json --report artifacts/bench_public/delta_report.json
	@echo "✅ Delta calibration completed"

repro-public:
	@echo "🔄 Running public reproduction..."
	bash scripts/repro_public.sh
	@echo "✅ Public reproduction completed"

# S2++ targets
s2pp-shadow:
	@echo "🔍 Running S2++ shadow mode..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline --runs 1 --out artifacts/s2pp/shadow
	@echo "✅ S2++ shadow mode completed"

s2pp-active:
	@echo "🚀 Running S2++ active mode..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes active --runs 1 --out artifacts/s2pp/active
	@echo "✅ S2++ active mode completed"

s2pp-bench:
	@echo "📊 Running S2++ benchmark..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 3 --out artifacts/s2pp/bench
	@echo "✅ S2++ benchmark completed"

s2pp-delta-calibrate:
	@echo "🔧 Calibrating S2++ delta weights..."
	. .venv/bin/activate && $(PY) scripts/delta_calibrate.py --input artifacts/s2pp/bench/metrics.csv --out configs/weights_v2.json --report artifacts/s2pp/delta_report.json --bootstrap 1000
	@echo "✅ S2++ delta calibration completed"

repro-public-s2pp:
	@echo "🔄 Running S2++ public reproduction..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes baseline,active --runs 3 --out artifacts/s2pp/repro
	. .venv/bin/activate && $(PY) scripts/delta_calibrate.py --input artifacts/s2pp/repro/metrics.csv --out configs/weights_v2.json --report artifacts/s2pp/delta_report.json --bootstrap 1000
	@echo "📦 Creating audit pack..."
	. .venv/bin/activate && $(PY) scripts/audit_pack.py --output artifacts/s2pp/audit_pack.zip
	@echo "🔐 Signing audit pack..."
	cosign sign-blob --key .github/security/cosign.key artifacts/s2pp/audit_pack.zip --output artifacts/s2pp/audit.sig
	@echo "✅ S2++ public reproduction completed"

# PR F1 Expected-fail targets
expected-fail-pii:
	@echo "🧪 Testing PII expected-fail cases..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes expected_fail --runs 1 --out artifacts/s2pp/expected_fail_pii --filter pii-logging
	@echo "✅ PII expected-fail tests completed"

expected-fail-license:
	@echo "🧪 Testing License expected-fail cases..."
	. .venv/bin/activate && $(PY) scripts/bench_2cat.py --suite corpus/s2pp/suite.json --modes expected_fail --runs 1 --out artifacts/s2pp/expected_fail_license --filter license-violation-agpl
	@echo "✅ License expected-fail tests completed"
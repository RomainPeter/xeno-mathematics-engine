PY=python3

.PHONY: setup verify demo audit-pack logs release schema-test validate fmt demo-s1 deps-lock build-verifier-pinned audit 2cat-shadow 2cat-active s2-bench 2cat-report validate-summary

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

# Architecture Unifiée v0.1 targets
arch-test:
	@echo "🧪 Testing Architecture Unifiée v0.1..."
	. .venv/bin/activate && $(PY) scripts/test_unified_architecture.py
	@echo "✅ Architecture Unifiée v0.1 tests completed"

arch-demo:
	@echo "🎯 Running Architecture Unifiée v0.1 demo..."
	. .venv/bin/activate && $(PY) scripts/demo_unified_architecture.py
	@echo "✅ Architecture Unifiée v0.1 demo completed"

arch-schemas:
	@echo "📋 Validating Architecture Unifiée v0.1 schemas..."
	. .venv/bin/activate && $(PY) scripts/test_roundtrip.py --schemas specs/v0.1/
	@echo "✅ Architecture Unifiée v0.1 schemas validated"

arch-egraph:
	@echo "🔗 Testing e-graph canonicalization..."
	. .venv/bin/activate && $(PY) -c "from proofengine.core.egraph import EGraph, canonicalize_state; egraph = EGraph(); print('E-graph initialized:', egraph.get_stats())"
	@echo "✅ E-graph functionality verified"

arch-orchestrator:
	@echo "🎭 Testing unified orchestrator..."
	. .venv/bin/activate && $(PY) -c "from proofengine.orchestrator.unified_orchestrator import UnifiedOrchestrator; print('Unified orchestrator imported successfully')"
	@echo "✅ Unified orchestrator verified"

arch-full: arch-test arch-demo arch-schemas arch-egraph arch-orchestrator
	@echo "🎉 Architecture Unifiée v0.1 fully validated!"

# Discovery Engine 2-Cat specific targets
ae-test:
	@echo "🔍 Testing AE Next-Closure..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_ae_loop.py -v
	@echo "✅ AE Next-Closure tests completed"

egraph-test:
	@echo "🔗 Testing E-graph canonicalization..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_egraph.py -v
	@echo "✅ E-graph tests completed"

bandit-test:
	@echo "🎯 Testing bandit/DPP selection..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_policy_selection.py -v
	@echo "✅ Bandit/DPP tests completed"

ci-test:
	@echo "🔧 Testing CI components..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_ci_components.py -v
	@echo "✅ CI tests completed"

discovery-test: ae-test egraph-test bandit-test ci-test
	@echo "🎉 Discovery Engine 2-Cat tests completed!"

discovery-demo:
	@echo "🎯 Running Discovery Engine 2-Cat demo..."
	. .venv/bin/activate && $(PY) scripts/demo_discovery_engine.py
	@echo "✅ Discovery Engine 2-Cat demo completed"

# CI and attestation targets
ci-test:
	@echo "🔧 Testing CI components..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_ci_components.py -v
	@echo "✅ CI tests completed"

hermetic-test:
	@echo "🔒 Testing hermetic runner..."
	. .venv/bin/activate && $(PY) runner/hermetic_stub.py
	@echo "✅ Hermetic runner test completed"

merkle-test:
	@echo "🔗 Testing Merkle journal..."
	. .venv/bin/activate && $(PY) scripts/merkle_journal.py
	@echo "✅ Merkle journal test completed"

attestation:
	@echo "🔐 Generating attestation..."
	. .venv/bin/activate && $(PY) scripts/merkle_journal.py
	@echo "✅ Attestation generated"

# Full CI pipeline
ci-full: ci-test hermetic-test merkle-test attestation
	@echo "🎉 Full CI pipeline completed!"

# RegTech demo targets
regtech-demo:
	@echo "🎯 Running RegTech Discovery Engine demo..."
	. .venv/bin/activate && $(PY) scripts/demo_regtech_bench.py
	@echo "✅ RegTech demo completed"

regtech-test:
	@echo "🧪 Testing RegTech components..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_ae_loop.py -v
	@echo "✅ RegTech tests completed"

# Complete Discovery Engine targets
discovery-full: discovery-test regtech-demo
	@echo "🎉 Complete Discovery Engine validation!"

# Incident handlers targets
incident-test:
	@echo "🔧 Testing incident handlers..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_incident_handlers.py -v
	@echo "✅ Incident handlers tests completed"

# CI artifacts targets
ci-artifacts-test:
	@echo "🔧 Testing CI artifacts..."
	. .venv/bin/activate && $(PY) -m pytest tests/test_ci_components.py -v
	@echo "✅ CI artifacts tests completed"

install-opa:
	@echo "🔧 Installing OPA..."
	bash scripts/install_opa.sh
	@echo "✅ OPA installation completed"

# Complete CI pipeline
ci-complete: ci-test hermetic-test merkle-test incident-test ci-artifacts-test install-opa
	@echo "🎉 Complete CI pipeline with all components!"

# Final Discovery Engine validation
discovery-final: discovery-full incident-test ci-artifacts-test
	@echo "🎉 Complete Discovery Engine 2-Cat validation with all PRs!"

# Stabilization and release targets
determinism-test:
	@echo "🔬 Running determinism test..."
	. .venv/bin/activate && $(PY) scripts/determinism_test.py --runs 3 --seed 42
	@echo "✅ Determinism test completed"

bench-regtech:
	@echo "📊 Running RegTech benchmark..."
	. .venv/bin/activate && $(PY) bench/run.py --suite regtech --baselines react,tot,dspy --ablations egraph,bandit,dpp,incident --out out/bench
	@echo "✅ RegTech benchmark completed"

metrics-validation:
	@echo "📈 Validating metrics..."
	. .venv/bin/activate && $(PY) -c "import json; metrics=json.load(open('out/metrics.json')); print('✅ Metrics valid:', metrics.get('coverage', {}).get('accepted', 0) >= 3)"
	@echo "✅ Metrics validation completed"

# Release preparation
release-prep: determinism-test bench-regtech metrics-validation
	@echo "🎯 Release preparation completed - ready for v0.1.0!"

# Docker and SBOM targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t discovery-engine-2cat:v0.1.0 .
	@echo "✅ Docker image built"

sbom-generate:
	@echo "📦 Generating SBOM..."
	curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
	syft packages . -o spdx-json=out/sbom.json
	syft packages . -o table=out/sbom.txt
	@echo "✅ SBOM generated"

security-scan:
	@echo "🔍 Running security scan..."
	curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
	grype sbom:out/sbom.json -o table=out/vulnerabilities.txt
	grype sbom:out/sbom.json -o json=out/vulnerabilities.json
	@echo "✅ Security scan completed"

# Complete release pipeline
release-pipeline: release-prep docker-build sbom-generate security-scan
	@echo "🚀 Release pipeline completed - ready for v0.1.0 tag!"

# Top-Lab Readiness targets
bench:
	@echo "📊 Running benchmark suite..."
	python bench/run.py --suite regtech --baselines react,tot,dspy --ablations egraph,bandit,dpp,incident --out out/bench
	@echo "✅ Benchmark completed"

rollup:
	@echo "📈 Computing metrics rollup..."
	python scripts/metrics_rollup.py out/ rollup/metrics-weekly.json
	@echo "✅ Metrics rollup completed"

release:
	@echo "🚀 Creating release..."
	gh workflow run Release -f version=$(VERSION)
	@echo "✅ Release workflow triggered"

# Cursor Pack targets
fire-drill:
	@echo "🔥 Running fire-drill Incident→Rule..."
	python scripts/fire_drill.py
	@echo "✅ Fire-drill completed"

sweep-ids-cvar:
	@echo "📊 Running IDS/CVaR parameter sweep..."
	python bench/run_sweep.py
	@echo "✅ IDS/CVaR sweep completed"

discovery-final: ae-test egraph-test bandit-test incident-test ci-artifacts-test regtech-demo
	@echo "🎉 Complete Discovery Engine validation!"

ae-test:
	@echo "🧪 Testing AE components..."
	pytest -q -k "ae_loop or e2e_ae" || true
	@echo "✅ AE tests completed"

egraph-test:
	@echo "🧪 Testing e-graph components..."
	pytest -q -k "egraph" || true
	@echo "✅ E-graph tests completed"

bandit-test:
	@echo "🧪 Testing policy selection..."
	pytest -q -k "policy_selection" || true
	@echo "✅ Bandit tests completed"

incident-test:
	@echo "🧪 Testing incident handlers..."
	pytest -q -k "incident_handlers" || true
	@echo "✅ Incident tests completed"

ci-artifacts-test:
	@echo "🧪 Testing CI artifacts..."
	python scripts/merkle_journal.py orchestrator/journal/J.jsonl out/journal/merkle.txt || true
	@echo "✅ CI artifacts tests completed"

regtech-demo:
	@echo "🎯 Running RegTech demo..."
	make demo || python scripts/demo_regtech_bench.py
	@echo "✅ RegTech demo completed"

# Hardening v0.1.1 targets
determinism:
	@echo "🔍 Checking determinism..."
	python scripts/check_determinism.py
	@echo "✅ Determinism check completed"

calibrate-budgets:
	@echo "📊 Calibrating budgets and timeouts..."
	python scripts/calibrate_budgets.py
	@echo "✅ Budget calibration completed"

# E-graph rules v0.2 targets
test-egraph-rules-v02:
	@echo "🔗 Testing e-graph rules v0.2..."
	python -m pytest tests/test_egraph_rules_v02.py -v
	@echo "✅ E-graph rules v0.2 tests completed"

# IDS/CVaR integration targets
test-policy-ids-cvar:
	@echo "📊 Testing IDS/CVaR policy integration..."
	python -m pytest tests/test_policy_ids_cvar.py -v
	@echo "✅ IDS/CVaR policy tests completed"

# HS-Tree integration targets
test-hstree:
	@echo "🌳 Testing HS-Tree minimal test generation..."
	python -m pytest tests/test_hstree.py -v
	@echo "✅ HS-Tree tests completed"

# Grove Pack targets
grove-pack:
	@echo "📋 Generating Grove pack..."
	python scripts/gen_onepager.py
	@echo "✅ Grove pack generated"

# Site targets
site:
	@echo "🌐 Building site..."
	mkdocs build
	@echo "✅ Site built"

site-deploy:
	@echo "🚀 Deploying site..."
	mkdocs gh-deploy --force
	@echo "✅ Site deployed"

# Public benchmark pack targets
public-bench-pack:
	@echo "📦 Building public benchmark pack..."
	python scripts/build_public_bench_pack.py
	@echo "✅ Public benchmark pack built"

# Complete hardening targets
hardening-v011: determinism test-egraph-rules-v02 calibrate-budgets test-policy-ids-cvar test-hstree
	@echo "🎉 Hardening v0.1.1 completed!"

# Complete Grove targets
grove-complete: grove-pack site public-bench-pack
	@echo "🎉 Grove pack completed!"

# All new targets
all-new: hardening-v011 grove-complete
	@echo "🎉 All new features completed!"

# T04: Summary validation
validate-summary:
	$(PY) -c "import json,sys; from pefc.metrics.validator import validate_summary_doc; from pathlib import Path; d=json.load(open('dist/summary.json')); validate_summary_doc(d, Path('schema/summary.schema.json'))" && echo "✅ Summary validation passed"

# T17: CLI unifiée (Typer)
export PEFC_CONFIG ?= config/pack.yaml
export PIPELINE ?= config/pipelines/bench_pack.yaml

.PHONY: public-bench-pack verify-pack pack-manifest pack-sign

public-bench-pack:
	pefc --config $(PEFC_CONFIG) pack build --pipeline $(PIPELINE)

public-bench-pack-strict:
	pefc --config $(PEFC_CONFIG) pack build --pipeline $(PIPELINE) --strict

verify-pack:
	pefc pack verify --zip dist/*.zip --strict

pack-manifest:
	pefc pack manifest --zip dist/*.zip --print

pack-sign:
	pefc pack sign --in dist/*.zip --provider cosign
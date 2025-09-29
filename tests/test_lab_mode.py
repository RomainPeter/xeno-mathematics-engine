"""
Lab mode determinism and artifact smoke tests.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from pefc.events import EventBusConfig, StructuredEventBus, FileJSONLSink
from orchestrator.orchestrator_lite import OrchestratorLite, OrchestratorLiteConfig
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from orchestrator.adapters.llm_stub import LLMStub
from orchestrator.adapters.verifier_stub import VerifierStub


async def _run_once(seed: int, audit_dir: Path) -> Path:
    bus = StructuredEventBus(
        config=EventBusConfig(
            buffer_size=4096, sinks=["file"], file_path=str(audit_dir / "journal.jsonl")
        )
    )
    bus.add_sink(FileJSONLSink(str(audit_dir / "journal.jsonl")))
    ae = NextClosureEngine()
    cegis = AsyncCegisEngine(
        LLMStub(seed=seed),
        VerifierStub(
            [{"valid": True, "confidence": 0.9, "evidence": {}, "metrics": {}}]
        ),
    )
    cfg = OrchestratorLiteConfig(
        ae_timeout=5.0,
        cegis_max_iterations=1,
        cegis_propose_timeout=5.0,
        cegis_verify_timeout=5.0,
        cegis_refine_timeout=5.0,
    )
    orch = OrchestratorLite(cfg, ae, cegis, event_bus=bus)
    domain_spec = {"objects": ["o1"], "attributes": ["a1"], "incidence": {}}
    await orch.run(domain_spec, {"verify_timeout": 5.0})
    return audit_dir / "journal.jsonl"


def _load_types(journal: Path):
    types = []
    if not journal.exists():
        return types
    for line in journal.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            types.append(ev.get("type"))
        except Exception:
            continue
    return types


def test_lab_determinism_by_seed():
    with tempfile.TemporaryDirectory() as d:
        # run 1
        out1 = Path(d) / "run1"
        out1.mkdir(parents=True, exist_ok=True)
        asyncio.run(_run_once(seed=123, audit_dir=out1))
        # run 2 with same seed
        out2 = Path(d) / "run2"
        out2.mkdir(parents=True, exist_ok=True)
        asyncio.run(_run_once(seed=123, audit_dir=out2))

        types1 = _load_types(out1 / "journal.jsonl")
        types2 = _load_types(out2 / "journal.jsonl")
        assert types1 == types2


def test_lab_artifacts_written():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "run"
        out.mkdir(parents=True, exist_ok=True)
        journal = asyncio.run(_run_once(seed=42, audit_dir=out))
        assert journal.exists()
        assert journal.stat().st_size > 0

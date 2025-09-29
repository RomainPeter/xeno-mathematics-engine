"""
Lab mode CLI to run orchestrator deterministically with fixtures and stubs.
"""

import argparse
import json
import uuid
from pathlib import Path

from pefc.events import EventBusConfig, StructuredEventBus, FileJSONLSink
from orchestrator.orchestrator import Orchestrator, OrchestratorConfig
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from orchestrator.adapters.llm_stub import LLMStub
from orchestrator.adapters.verifier_stub import VerifierStub


def main():
    parser = argparse.ArgumentParser(description="Lab mode orchestrator")
    parser.add_argument("--lab", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--time-budget", type=float, default=10.0)
    parser.add_argument("--max-iters", type=int, default=3)
    parser.add_argument("--hermetic", action="store_true")
    parser.add_argument("--audit-dir", type=str, default="./_audit")
    args = parser.parse_args()

    run_id = f"r-{uuid.uuid4().hex[:8]}"
    audit_dir = Path(args.audit_dir) / run_id
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Event bus to file
    events_path = str(audit_dir / "journal.jsonl")
    bus = StructuredEventBus(
        config=EventBusConfig(buffer_size=4096, sinks=["file"], file_path=events_path)
    )
    bus.add_sink(FileJSONLSink(events_path))

    # Engines and stubs
    ae = NextClosureEngine()
    cegis = AsyncCegisEngine(LLMStub(seed=args.seed), VerifierStub())

    cfg = OrchestratorConfig(
        ae_timeout=args.time_budget,
        cegis_max_iterations=args.max_iters,
        cegis_propose_timeout=args.time_budget,
        cegis_verify_timeout=args.time_budget,
        cegis_refine_timeout=args.time_budget,
        audit_dir=str(audit_dir),
    )

    orch = Orchestrator(
        config=cfg,
        ae_engine=ae,
        cegis_engine=cegis,
        llm_adapter=None,
        verifier=None,
        event_bus=bus,
    )

    # Domain spec: load toy FCA if present
    fca_path = Path("fixtures/fca/context_4x4.json")
    domain_spec = {}
    if fca_path.exists():
        domain_spec = json.loads(fca_path.read_text())

    budgets = {"verify_timeout": args.time_budget}
    thresholds = {}

    # Run orchestrator
    import asyncio

    asyncio.run(orch.run(domain_spec, budgets, thresholds))
    print(f"Run artifacts in: {audit_dir}")


if __name__ == "__main__":
    main()

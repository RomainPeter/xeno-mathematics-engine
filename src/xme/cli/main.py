from typing import Optional, List
import uuid
import asyncio
from datetime import datetime, timezone
import typer
from rich import print
import orjson
from xme.psp.schema import PSP, load_psp, save_psp
from xme.pcap.store import PCAPStore, PCAPEntry
from xme.orchestrator.state import RunState, Budgets
from xme.orchestrator.event_bus import EventBus
from xme.orchestrator.loops.ae import run_ae
from xme.orchestrator.loops.cegis import run_cegis
from xme.orchestrator.scheduler import DiscoveryConfig, DiscoveryScheduler
from xme.pefc.pack import collect_inputs, build_manifest, write_zip, verify_pack
from pathlib import Path
import subprocess

app = typer.Typer(help="XME — Xeno-Math Engine CLI")
psp_app = typer.Typer(help="PSP commands")
pcap_app = typer.Typer(help="PCAP journal")
engine_app = typer.Typer(help="Engine ops")
ae_app = typer.Typer(help="AE operations")
cegis_app = typer.Typer(help="CEGIS operations")
discover_app = typer.Typer(help="Discovery operations")
pack_app = typer.Typer(help="Audit Pack operations")
app.add_typer(psp_app, name="psp")
app.add_typer(pcap_app, name="pcap")
app.add_typer(engine_app, name="engine")
app.add_typer(ae_app, name="ae")
app.add_typer(cegis_app, name="cegis")
app.add_typer(discover_app, name="discover")
app.add_typer(pack_app, name="pack")


@app.callback()
def main():
    print("[bold cyan]XME CLI[/bold cyan]")


@psp_app.command("validate")
def psp_validate(path: str):
    psp = load_psp(path)
    print("[green]PSP valid[/green]")
    print(f"Nodes: {psp.dag.nodes}, Edges: {psp.dag.edges}, Acyclic: {psp.dag.acyclic}")
    if psp.meta.theorem:
        print(f"Theorem: {psp.meta.theorem}")


@psp_app.command("schema")
def psp_schema(out: Optional[str] = typer.Option(None, "--out", help="Path to write JSON Schema")):
    schema = PSP.model_json_schema(PSP)
    payload = orjson.dumps(schema, option=orjson.OPT_SORT_KEYS)
    if out:
        Path(out).write_bytes(payload)
        print(f"[green]PSP JSON Schema written to {out}[/green]")
    else:
        import sys as _sys
        _sys.stdout.buffer.write(payload)


@psp_app.command("normalize")
def psp_normalize(path: str, out: Optional[str] = typer.Option(None, "--out")):
    p = load_psp(path)
    p.normalize()
    if out:
        save_psp(p, out)
        print(f"[green]Normalized PSP written to {out}[/green]")
    else:
        typer.echo(p.canonical_json())


@psp_app.command("topo")
def psp_topo(path: str, as_json: bool = typer.Option(False, "--json/--no-json")):
    p = load_psp(path)
    order = p.topo_sort()
    if as_json:
        typer.echo(orjson.dumps(order).decode())
    else:
        for n in order:
            typer.echo(n)


@pcap_app.command("new-run")
def pcap_new_run(out: str = typer.Option("artifacts/pcap", "--out")):
    store = PCAPStore.new_run(Path(out))
    print(f"[green]New run[/green] path={store.path}")


@pcap_app.command("log")
def pcap_log(
    run: str = typer.Option(..., "--run", help="Path to run .jsonl"),
    action: str = typer.Option(..., "--action"),
    actor: str = typer.Option("xme", "--actor"),
    level: str = typer.Option("S0", "--level"),
    psp_ref: Optional[str] = typer.Option(None, "--psp-ref"),
):
    store = PCAPStore(Path(run))
    entry = PCAPEntry(
        action=action,
        actor=actor,
        level=level,
        psp_ref=psp_ref,
        obligations={},
        deltas={},
        timestamp=datetime.now(timezone.utc),
    )
    stored = store.append(entry)
    print(f"[green]Logged[/green] hash={stored.hash} prev={stored.prev_hash}")


@pcap_app.command("merkle")
def pcap_merkle(run: str = typer.Option(..., "--run")):
    store = PCAPStore(Path(run))
    root = store.merkle_root()
    print(root or "")


@pcap_app.command("verify")
def pcap_verify(run: str = typer.Option(..., "--run")):
    store = PCAPStore(Path(run))
    ok, reason = store.verify()
    if not ok:
        print(f"[red]Verify failed[/red]: {reason}")
        raise typer.Exit(code=1)
    print("[green]Verify OK[/green]")


@ae_app.command("demo")
def ae_demo(
    context: str = typer.Option(..., "--context"),
    out: str = typer.Option("artifacts/psp/ae_demo.json", "--out"),
    run: str = typer.Option("", "--run", help="PCAP run path; if empty, a new run is created"),
    ae_ms: int = typer.Option(1500, "--ae-ms", help="AE timeout budget (ms)")
):
    """Exécute une démonstration AE sur un contexte FCA."""
    out_psp = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())), 
        budgets=Budgets(ae_ms=ae_ms)
    )
    bus = EventBus()
    asyncio.run(run_ae(context, state, bus, store, out_psp))
    print(f"[green]AE demo OK[/green] PSP={out_psp}")


@cegis_app.command("demo")
def cegis_demo(
    secret: str = typer.Option(..., "--secret", help="Secret bitvector to synthesize"),
    max_iters: int = typer.Option(16, "--max-iters", help="Maximum iterations"),
    out: str = typer.Option("artifacts/cegis/result.json", "--out"),
    run: str = typer.Option("", "--run", help="PCAP run path; if empty, a new run is created"),
    cegis_ms: int = typer.Option(5000, "--cegis-ms", help="CEGIS timeout budget (ms)")
):
    """Exécute une démonstration CEGIS pour synthétiser un vecteur de bits secret."""
    out_path = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())), 
        budgets=Budgets(cegis_ms=cegis_ms)
    )
    bus = EventBus()
    asyncio.run(run_cegis(secret, max_iters, state, bus, store, out_path))
    print(f"[green]CEGIS demo OK[/green] result={out_path}")


@discover_app.command("demo")
def discover_demo(
    turns: int = typer.Option(5, "--turns", help="Number of discovery turns"),
    ae_context: str = typer.Option("examples/fca/context_4x4.json", "--ae-context", help="FCA context for AE"),
    secret: str = typer.Option("10110", "--secret", help="Secret bitvector for CEGIS"),
    out: str = typer.Option("artifacts/discovery/run.json", "--out"),
    run: str = typer.Option("", "--run", help="PCAP run path; if empty, a new run is created"),
    epsilon: float = typer.Option(0.1, "--epsilon", help="Exploration rate (0.0-1.0)"),
    ae_ms: int = typer.Option(1500, "--ae-ms", help="AE timeout budget (ms)"),
    cegis_ms: int = typer.Option(5000, "--cegis-ms", help="CEGIS timeout budget (ms)")
):
    """Exécute une démonstration discovery avec sélection AE/CEGIS."""
    out_path = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())), 
        budgets=Budgets(ae_ms=ae_ms, cegis_ms=cegis_ms)
    )
    bus = EventBus()
    
    # Configuration discovery
    config = DiscoveryConfig(
        turns=turns,
        ae_context=ae_context,
        cegis_secret=secret,
        ae_budget_ms=ae_ms,
        cegis_budget_ms=cegis_ms,
        epsilon=epsilon
    )
    
    # Scheduler discovery
    scheduler = DiscoveryScheduler(config)
    
    # Exécution
    results = asyncio.run(scheduler.run_discovery(state, bus, store, out_path.parent))
    
    # Sauvegarde des résultats
    out_path.write_text(orjson.dumps(results).decode())
    
    print(f"[green]Discovery demo OK[/green] result={out_path}")
    print(f"[green]Best arm[/green] {results['best_arm']}")
    print(f"[green]Total reward[/green] {results['total_reward']}")


@pack_app.command("build")
def pack_build(
    include: List[str] = typer.Option([], "--include", help="Glob patterns to include"),
    out: str = typer.Option("dist/", "--out", help="Output directory"),
    run_path: Optional[str] = typer.Option(None, "--run-path", help="PCAP run path")
):
    """Construit un Audit Pack avec manifest et vérification d'intégrité."""
    # Collecter les fichiers
    inputs = collect_inputs(include)
    if not inputs:
        print("[yellow]No files found to include in pack[/yellow]")
        return
    
    # Construire le manifest
    manifest = build_manifest(inputs, run_path)
    
    # Écrire le pack ZIP
    pack_path = write_zip(manifest, out)
    
    print(f"[green]Pack built[/green] path={pack_path}")
    print(f"[green]Files included[/green] count={len(manifest.files)}")
    print(f"[green]Merkle root[/green] {manifest.merkle_root}")


@pack_app.command("verify")
def pack_verify(
    pack: str = typer.Option(..., "--pack", help="Path to pack ZIP file")
):
    """Vérifie l'intégrité d'un Audit Pack."""
    pack_path = Path(pack)
    if not pack_path.exists():
        print(f"[red]Pack not found[/red] {pack_path}")
        raise typer.Exit(code=1)
    
    ok, reason = verify_pack(pack_path)
    if not ok:
        print(f"[red]Verify failed[/red] {reason}")
        raise typer.Exit(code=1)
    
    print(f"[green]Pack verified[/green] {pack_path}")


@engine_app.command("verify-2cat")
def verify_2cat():
    script = Path("scripts/verify_2cat_pack.sh")
    if not script.exists():
        typer.echo("Missing scripts/verify_2cat_pack.sh", err=True)
        raise typer.Exit(code=2)
    subprocess.run(["bash", str(script)], check=True)
    print("[green]2cat pack verified[/green]")


if __name__ == "__main__":
    app()

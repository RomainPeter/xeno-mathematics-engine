from typing import Optional
import uuid
import asyncio
from datetime import datetime, timezone
import typer
from rich import print
from xme.psp.schema import PSP, load_psp, save_psp
from xme.pcap.store import PCAPStore, PCAPEntry
from xme.orchestrator.state import RunState, Budgets
from xme.orchestrator.event_bus import EventBus
from xme.orchestrator.loops.ae import run_ae
from pathlib import Path
import subprocess

app = typer.Typer(help="XME — Xeno-Math Engine CLI")
psp_app = typer.Typer(help="PSP commands")
pcap_app = typer.Typer(help="PCAP journal")
engine_app = typer.Typer(help="Engine ops")
ae_app = typer.Typer(help="AE operations")
app.add_typer(psp_app, name="psp")
app.add_typer(pcap_app, name="pcap")
app.add_typer(engine_app, name="engine")
app.add_typer(ae_app, name="ae")


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

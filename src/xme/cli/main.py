from typing import Optional
import uuid
from datetime import datetime, timezone
import typer
from rich import print
from xme.psp.schema import load_psp
from xme.pcap.store import PCAPStore, PCAPEntry
from pathlib import Path
import subprocess

app = typer.Typer(help="XME — Xeno-Math Engine CLI")
psp_app = typer.Typer(help="PSP commands")
pcap_app = typer.Typer(help="PCAP journal")
engine_app = typer.Typer(help="Engine ops")
app.add_typer(psp_app, name="psp")
app.add_typer(pcap_app, name="pcap")
app.add_typer(engine_app, name="engine")


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


@pcap_app.command("log")
def pcap_log(
    action: str,
    actor: str = "xme",
    psp_ref: Optional[str] = None,
    out: str = "artifacts/pcap",
):
    run_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    store = PCAPStore(Path(out) / f"run-{ts}.jsonl")
    store.append(
        PCAPEntry(
            action=action,
            actor=actor,
            psp_ref=psp_ref,
            obligations={},
            deltas={},
            timestamp=datetime.now(timezone.utc),
        )
    )
    print(f"[green]Logged[/green] run_id={run_id}")


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

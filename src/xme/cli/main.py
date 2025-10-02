import asyncio
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import orjson
import typer
from rich import print

from xme.adapters.logger import log_verdict
from xme.discovery_engine_2cat.config import (AEConfig, BudgetsConfig,
                                              CEGISConfig,
                                              DiscoveryEngine2CatConfig,
                                              OutputsConfig, PackConfig)
from xme.discovery_engine_2cat.runner import run_discovery_engine_2cat
from xme.egraph.canon import canonicalize, compare_expressions
from xme.metrics.delta import aggregate_run_delta
from xme.metrics.summarize import export_summary_json, summarize_run
from xme.orchestrator.event_bus import EventBus
from xme.orchestrator.loops.ae import run_ae
from xme.orchestrator.loops.cegis import run_cegis
from xme.orchestrator.scheduler import DiscoveryConfig, DiscoveryScheduler
from xme.orchestrator.state import Budgets, RunState
from xme.pcap.store import PCAPEntry, PCAPStore
from xme.pefc.pack import (build_manifest, collect_inputs, verify_pack,
                           write_zip)
from xme.psp.schema import PSP, load_psp, save_psp
from xme.verifier.base import Verifier, create_obligation
from xme.verifier.psp_checks import get_psp_obligations
from xme.verifier.report import Report, save_report

app = typer.Typer(help="XME — Xeno-Math Engine CLI")
psp_app = typer.Typer(help="PSP commands")
pcap_app = typer.Typer(help="PCAP journal")
engine_app = typer.Typer(help="Engine ops")
ae_app = typer.Typer(help="AE operations")
cegis_app = typer.Typer(help="CEGIS operations")
discover_app = typer.Typer(help="Discovery operations")
egraph_app = typer.Typer(help="E-graph operations")
pack_app = typer.Typer(help="Audit Pack operations")
verify_app = typer.Typer(help="Verification operations")
metrics_app = typer.Typer(help="Metrics operations")
discovery_2cat_app = typer.Typer(help="Discovery Engine 2Cat operations")
app.add_typer(psp_app, name="psp")
app.add_typer(pcap_app, name="pcap")
app.add_typer(engine_app, name="engine")
app.add_typer(ae_app, name="ae")
app.add_typer(cegis_app, name="cegis")
app.add_typer(discover_app, name="discover")
app.add_typer(egraph_app, name="egraph")
app.add_typer(pack_app, name="pack")
app.add_typer(verify_app, name="verify")
app.add_typer(metrics_app, name="metrics")
app.add_typer(discovery_2cat_app, name="2cat")


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
    ae_ms: int = typer.Option(1500, "--ae-ms", help="AE timeout budget (ms)"),
):
    """Exécute une démonstration AE sur un contexte FCA."""
    out_psp = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())),
        budgets=Budgets(ae_ms=ae_ms),
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
    cegis_ms: int = typer.Option(5000, "--cegis-ms", help="CEGIS timeout budget (ms)"),
):
    """Exécute une démonstration CEGIS pour synthétiser un vecteur de bits secret."""
    out_path = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())),
        budgets=Budgets(cegis_ms=cegis_ms),
    )
    bus = EventBus()
    asyncio.run(run_cegis(secret, max_iters, state, bus, store, out_path))
    print(f"[green]CEGIS demo OK[/green] result={out_path}")


@discover_app.command("demo")
def discover_demo(
    turns: int = typer.Option(5, "--turns", help="Number of discovery turns"),
    ae_context: str = typer.Option(
        "examples/fca/context_4x4.json", "--ae-context", help="FCA context for AE"
    ),
    secret: str = typer.Option("10110", "--secret", help="Secret bitvector for CEGIS"),
    out: str = typer.Option("artifacts/discovery/run.json", "--out"),
    run: str = typer.Option("", "--run", help="PCAP run path; if empty, a new run is created"),
    epsilon: float = typer.Option(0.1, "--epsilon", help="Exploration rate (0.0-1.0)"),
    ae_ms: int = typer.Option(1500, "--ae-ms", help="AE timeout budget (ms)"),
    cegis_ms: int = typer.Option(5000, "--cegis-ms", help="CEGIS timeout budget (ms)"),
):
    """Exécute une démonstration discovery avec sélection AE/CEGIS."""
    out_path = Path(out)
    store = PCAPStore(Path(run)) if run else PCAPStore.new_run(Path("artifacts/pcap"))
    state = RunState(
        run_id=(store.path.stem if hasattr(store, "path") else str(uuid.uuid4())),
        budgets=Budgets(ae_ms=ae_ms, cegis_ms=cegis_ms),
    )
    bus = EventBus()

    # Configuration discovery
    config = DiscoveryConfig(
        turns=turns,
        ae_context=ae_context,
        cegis_secret=secret,
        ae_budget_ms=ae_ms,
        cegis_budget_ms=cegis_ms,
        epsilon=epsilon,
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


@egraph_app.command("canon")
def egraph_canon(
    input_file: str = typer.Option(..., "--in", help="Input JSON file"),
    output_file: str = typer.Option(..., "--out", help="Output canonical JSON file"),
):
    """Canonicalise une expression et génère sa signature."""
    import orjson

    # Lire l'expression d'entrée
    with open(input_file, "rb") as f:
        expr = orjson.loads(f.read())

    # Canonicaliser
    result = canonicalize(expr)

    # Créer le répertoire de sortie si nécessaire
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le résultat
    with open(output_file, "wb") as f:
        f.write(orjson.dumps(result, option=orjson.OPT_INDENT_2))

    print(f"[green]Canonicalized[/green] input={input_file} output={output_file}")
    print(f"[green]Signature[/green] {result['sig']}")


@egraph_app.command("equal")
def egraph_equal(
    expr_a: str = typer.Option(..., "--a", help="First expression JSON file"),
    expr_b: str = typer.Option(..., "--b", help="Second expression JSON file"),
):
    """Vérifie si deux expressions sont structurellement égales."""
    import orjson

    # Lire les expressions
    with open(expr_a, "rb") as f:
        expr1 = orjson.loads(f.read())

    with open(expr_b, "rb") as f:
        expr2 = orjson.loads(f.read())

    # Comparer
    result = compare_expressions(expr1, expr2)

    if result["equal"]:
        print(f"[green]Equal[/green] {expr_a} == {expr_b}")
        print(f"[green]Signature[/green] {result['sig1']}")
        sys.exit(0)
    else:
        print(f"[red]Different[/red] {expr_a} != {expr_b}")
        print(f"[yellow]Signature A[/yellow] {result['sig1']}")
        print(f"[yellow]Signature B[/yellow] {result['sig2']}")
        sys.exit(1)


@pack_app.command("build")
def pack_build(
    include: List[str] = typer.Option([], "--include", help="Glob patterns to include"),
    out: str = typer.Option("dist/", "--out", help="Output directory"),
    run_path: Optional[str] = typer.Option(None, "--run-path", help="PCAP run path"),
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
def pack_verify(pack: str = typer.Option(..., "--pack", help="Path to pack ZIP file")):
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


@verify_app.command("psp")
def verify_psp(
    input_file: str = typer.Option(..., "--in", help="Input PSP JSON file"),
    level: str = typer.Option("S0", "--level", help="Verification level (S0, S1)"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output report JSON file"),
    pcap_run: Optional[str] = typer.Option(None, "--run", help="PCAP run path for logging"),
):
    """Vérifie un PSP avec les obligations S0/S1."""
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[red]Input file not found[/red] {input_path}")
        raise typer.Exit(code=1)

    # Charger le PSP
    try:
        with open(input_path, "rb") as f:
            psp_data = orjson.loads(f.read())
    except Exception as e:
        print(f"[red]Error loading PSP[/red] {e}")
        raise typer.Exit(code=1)

    # Créer le vérificateur et enregistrer les obligations PSP
    verifier = Verifier()
    for obligation_id, level_obligation, check_func, description in get_psp_obligations():
        obligation = create_obligation(obligation_id, level_obligation, check_func, description)
        verifier.register_obligation(obligation)

    # Exécuter les vérifications
    report = verifier.run_by_level(psp_data, level)

    # Loguer les verdicts dans PCAP si spécifié
    if pcap_run:
        store = PCAPStore(Path(pcap_run))
        for result in report.results:
            log_verdict(
                store=store,
                obligation_id=result.obligation_id,
                level=result.level,
                ok=result.ok,
                details=result.details,
            )

    # Sauvegarder le rapport si spécifié
    if output_file:
        save_report(report, output_file)
        print(f"[green]Report saved[/green] {output_file}")

    # Afficher le résumé
    summary = report.summary()
    print("[bold]Verification Summary[/bold]")
    print(f"Level: {level}")
    print(f"Total: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Overall: {'[green]PASS[/green]' if report.ok_all else '[red]FAIL[/red]'}")

    # Afficher les détails des échecs
    if not report.ok_all:
        print("[bold red]Failed Obligations:[/bold red]")
        for result in report.get_failed_results():
            print(
                f"  - {result.obligation_id} ({result.level}): {result.details.get('message', 'No message')}"
            )

    # Code de retour
    if not report.ok_all:
        raise typer.Exit(code=1)


@verify_app.command("run")
def verify_run(
    run_path: str = typer.Option(..., "--run", help="PCAP run path"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output report JSON file"),
):
    """Vérifie un run PCAP (chain & merkle + obligations)."""
    run_file = Path(run_path)
    if not run_file.exists():
        print(f"[red]Run file not found[/red] {run_file}")
        raise typer.Exit(code=1)

    # Charger le store PCAP
    try:
        store = PCAPStore(run_file)
        entries = list(store.read_all())
    except Exception as e:
        print(f"[red]Error loading PCAP run[/red] {e}")
        raise typer.Exit(code=1)

    # Vérifier la chaîne et le Merkle (basique)
    chain_ok = True
    chain_details = {}

    if len(entries) > 1:
        # Vérifier la cohérence des hashes
        for i in range(1, len(entries)):
            prev_entry = entries[i - 1]
            curr_entry = entries[i]

            if prev_entry.get("hash") != curr_entry.get("prev_hash"):
                chain_ok = False
                chain_details["error"] = f"Hash mismatch at entry {i}"
                break

    # Collecter les obligations loguées
    obligations = {}
    for entry in entries:
        if entry.get("action") == "verification_verdict":
            entry_obligations = entry.get("obligations", {})
            for key, value in entry_obligations.items():
                if not key.endswith("_message") and not key.endswith(
                    "_error"
                ):  # Filtrer les détails
                    obligations[key] = value

    # Créer le rapport
    report = Report()

    # Ajouter le résultat de vérification de la chaîne
    report.add_result(
        obligation_id="pcap_chain_consistency",
        level="S0",
        ok=chain_ok,
        details=chain_details if not chain_ok else {"message": "PCAP chain is consistent"},
    )

    # Ajouter les obligations loguées
    for obligation_id, result in obligations.items():
        report.add_result(
            obligation_id=obligation_id,
            level="S0",  # Par défaut
            ok=result == "True",
            details={"message": f"Logged obligation: {result}"},
        )

    # Sauvegarder le rapport si spécifié
    if output_file:
        save_report(report, output_file)
        print(f"[green]Report saved[/green] {output_file}")

    # Afficher le résumé
    print("[bold]PCAP Run Verification Summary[/bold]")
    print(f"Total entries: {len(entries)}")
    print(f"Chain consistent: {'[green]YES[/green]' if chain_ok else '[red]NO[/red]'}")
    print(f"Logged obligations: {len(obligations)}")
    print(f"Overall: {'[green]PASS[/green]' if report.ok_all else '[red]FAIL[/red]'}")

    # Code de retour
    if not report.ok_all:
        raise typer.Exit(code=1)


@metrics_app.command("summarize")
def metrics_summarize(
    run_path: str = typer.Option(..., "--run", help="PCAP run path"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output JSON file"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Synthétise les métriques d'un run PCAP."""
    run_file = Path(run_path)
    if not run_file.exists():
        print(f"[red]Run file not found[/red] {run_file}")
        raise typer.Exit(code=1)

    # Générer le résumé
    summary = summarize_run(run_file)

    # Sauvegarder si spécifié
    if output_file:
        export_summary_json(summary, Path(output_file))
        print(f"[green]Summary saved[/green] {output_file}")

    # Afficher le résumé
    if json:
        print(orjson.dumps(summary, option=orjson.OPT_INDENT_2).decode())
    else:
        print("[bold]Metrics Summary[/bold]")
        print(f"Run: {summary['run_path']}")
        print(f"Total entries: {summary['total_entries']}")
        print(f"Incidents: {len(summary['incidents'])}")
        print(f"δ_run: {summary['deltas']['delta_run']:.3f}")
        print(f"Merkle root: {summary['merkle_root'] or 'N/A'}")
        print(f"Summary: {summary['summary']}")

        # Afficher les actions
        if summary["actions"]:
            print("[bold]Actions:[/bold]")
            for action, count in summary["actions"].items():
                print(f"  {action}: {count}")

        # Afficher les incidents
        if summary["incidents"]:
            print("[bold red]Incidents:[/bold red]")
            for incident in summary["incidents"]:
                print(f"  {incident['timestamp']}: {incident['action']} ({incident['type']})")


@metrics_app.command("delta")
def metrics_delta(
    run_path: str = typer.Option(..., "--run", help="PCAP run path"),
    phase: Optional[str] = typer.Option(None, "--phase", help="Specific phase to analyze"),
):
    """Calcule les métriques δ d'un run PCAP."""
    run_file = Path(run_path)
    if not run_file.exists():
        print(f"[red]Run file not found[/red] {run_file}")
        raise typer.Exit(code=1)

    # Calculer les δ
    delta_info = aggregate_run_delta(run_file)

    print("[bold]Delta Metrics[/bold]")
    print(f"Run: {run_file}")
    print(f"δ_run: {delta_info['delta_run']:.3f}")
    print(f"Total entries: {delta_info['total_entries']}")

    if phase:
        # Afficher le δ d'une phase spécifique
        phase_deltas = delta_info.get("deltas_by_phase", {})
        if phase in phase_deltas:
            print(f"δ_{phase}: {phase_deltas[phase]:.3f}")
        else:
            print(f"[yellow]Phase '{phase}' not found[/yellow]")
    else:
        # Afficher tous les δ par phase
        phase_deltas = delta_info.get("deltas_by_phase", {})
        if phase_deltas:
            print("[bold]Deltas by phase:[/bold]")
            for phase_name, delta_value in phase_deltas.items():
                print(f"  δ_{phase_name}: {delta_value:.3f}")

        phase_weights = delta_info.get("phase_weights", {})
        if phase_weights:
            print("[bold]Phase weights:[/bold]")
            for phase_name, weight in phase_weights.items():
                print(f"  {phase_name}: {weight}")


@metrics_app.command("compare")
def metrics_compare(
    run1: str = typer.Option(..., "--run1", help="First PCAP run path"),
    run2: str = typer.Option(..., "--run2", help="Second PCAP run path"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output comparison JSON file"),
):
    """Compare les métriques de deux runs PCAP."""
    run1_file = Path(run1)
    run2_file = Path(run2)

    if not run1_file.exists():
        print(f"[red]First run file not found[/red] {run1_file}")
        raise typer.Exit(code=1)

    if not run2_file.exists():
        print(f"[red]Second run file not found[/red] {run2_file}")
        raise typer.Exit(code=1)

    # Générer les résumés
    summary1 = summarize_run(run1_file)
    summary2 = summarize_run(run2_file)

    # Comparer
    from xme.metrics.summarize import compare_summaries

    comparison = compare_summaries(summary1, summary2)

    # Sauvegarder si spécifié
    if output_file:
        export_summary_json(comparison, Path(output_file))
        print(f"[green]Comparison saved[/green] {output_file}")

    # Afficher la comparaison
    print("[bold]Run Comparison[/bold]")
    print(f"Run 1: {run1_file}")
    print(f"Run 2: {run2_file}")
    print(f"Summary: {comparison['summary']}")

    delta_comp = comparison["delta_comparison"]
    print("[bold]Delta comparison:[/bold]")
    print(f"  Run 1 δ: {delta_comp['summary1']:.3f}")
    print(f"  Run 2 δ: {delta_comp['summary2']:.3f}")
    print(f"  Difference: {delta_comp['difference']:+.3f}")
    print(
        f"  Improvement: {'[green]Yes[/green]' if delta_comp['improvement'] else '[red]No[/red]'}"
    )

    entries_comp = comparison["entries_comparison"]
    print("[bold]Entries comparison:[/bold]")
    print(f"  Run 1: {entries_comp['summary1']}")
    print(f"  Run 2: {entries_comp['summary2']}")
    print(f"  Difference: {entries_comp['difference']:+d}")

    incidents_comp = comparison["incidents_comparison"]
    print("[bold]Incidents comparison:[/bold]")
    print(f"  Run 1: {incidents_comp['summary1']}")
    print(f"  Run 2: {incidents_comp['summary2']}")
    print(f"  Difference: {incidents_comp['difference']:+d}")


@discovery_2cat_app.command("run")
def discovery_2cat_run(
    config: str = typer.Option(..., "--config", help="Configuration YAML file"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output report JSON file"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Exécute le pipeline discovery-engine-2cat unifié."""
    config_path = Path(config)
    if not config_path.exists():
        print(f"[red]Configuration file not found[/red] {config_path}")
        raise typer.Exit(code=1)

    try:
        # Exécuter le pipeline
        result = asyncio.run(run_discovery_engine_2cat(config_path))

        # Sauvegarder le rapport si spécifié
        if output_file:
            with open(output_file, "wb") as f:
                f.write(orjson.dumps(result, option=orjson.OPT_INDENT_2))
            print(f"[green]Report saved[/green] {output_file}")

        # Afficher le résultat
        if json:
            print(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode())
        else:
            print("[bold]Discovery Engine 2Cat Pipeline[/bold]")
            print(f"Run ID: {result['run_id']}")
            print(f"Start: {result['start_time']}")
            print(f"End: {result['end_time']}")
            print(f"Success: {'[green]YES[/green]' if result['success'] else '[red]NO[/red]'}")

            # Afficher les résultats
            results = result["results"]
            print("[bold]Results:[/bold]")
            print(
                f"  AE: {'[green]SUCCESS[/green]' if results['ae']['success'] else '[red]FAILED[/red]'}"
            )
            print(
                f"  CEGIS: {'[green]SUCCESS[/green]' if results['cegis']['success'] else '[red]FAILED[/red]'}"
            )
            print(
                f"  Verification: {'[green]PASS[/green]' if results['verification']['success'] else '[red]FAIL[/red]'}"
            )

            # Afficher les métriques
            if "metrics" in results and "delta_run" in results["metrics"]:
                print(f"  δ_run: {results['metrics']['delta_run']:.3f}")

            # Afficher les artefacts
            artifacts = result["artifacts"]
            print("[bold]Artifacts:[/bold]")
            for name, path in artifacts.items():
                if path:
                    print(f"  {name}: {path}")

        # Code de retour
        if not result["success"]:
            raise typer.Exit(code=1)

    except Exception as e:
        print(f"[red]Pipeline execution failed[/red] {e}")
        raise typer.Exit(code=1)


@discovery_2cat_app.command("verify-pack")
def discovery_2cat_verify_pack(
    pack: str = typer.Option(..., "--pack", help="Pack ZIP file to verify"),
    output_file: Optional[str] = typer.Option(None, "--out", help="Output verification JSON file"),
    json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Vérifie l'intégrité d'un Audit Pack."""
    pack_path = Path(pack)
    if not pack_path.exists():
        print(f"[red]Pack file not found[/red] {pack_path}")
        raise typer.Exit(code=1)

    try:
        # Vérifier le pack
        verification_result = verify_pack(pack_path)

        # Sauvegarder le résultat si spécifié
        if output_file:
            with open(output_file, "wb") as f:
                f.write(orjson.dumps(verification_result, option=orjson.OPT_INDENT_2))
            print(f"[green]Verification saved[/green] {output_file}")

        # Afficher le résultat
        if json:
            print(orjson.dumps(verification_result, option=orjson.OPT_INDENT_2).decode())
        else:
            print("[bold]Pack Verification[/bold]")
            print(f"Pack: {pack_path}")
            print(
                f"Valid: {'[green]YES[/green]' if verification_result['valid'] else '[red]NO[/red]'}"
            )

            if verification_result["valid"]:
                print(f"Files: {verification_result['files_count']}")
                print(f"Merkle root: {verification_result['merkle_root']}")
                print(f"Size: {verification_result['total_size']} bytes")
            else:
                print(f"Error: {verification_result.get('error', 'Unknown error')}")

        # Code de retour
        if not verification_result["valid"]:
            raise typer.Exit(code=1)

    except Exception as e:
        print(f"[red]Pack verification failed[/red] {e}")
        raise typer.Exit(code=1)


@discovery_2cat_app.command("config")
def discovery_2cat_config(
    output_file: str = typer.Option(
        "config/pipelines/default.yaml", "--out", help="Output YAML file"
    ),
    template: bool = typer.Option(False, "--template", help="Generate template configuration"),
):
    """Génère un fichier de configuration par défaut."""
    try:
        # Créer une configuration par défaut
        config = DiscoveryEngine2CatConfig(
            ae=AEConfig(context="examples/fca/context_4x4.json"),
            cegis=CEGISConfig(secret="10110", max_iters=16),
            budgets=BudgetsConfig(ae_ms=1500, cegis_ms=1500),
            outputs=OutputsConfig(
                psp="artifacts/psp/2cat.json",
                run_dir="artifacts/pcap",
                metrics="artifacts/metrics/2cat.json",
                report="artifacts/reports/2cat.json",
            ),
            pack=PackConfig(
                out="dist/",
                include=[
                    "artifacts/psp/*.json",
                    "artifacts/pcap/run-*.jsonl",
                    "docs/psp.schema.json",
                ],
                name="2cat-pack",
            ),
        )

        # Sauvegarder la configuration
        output_path = Path(output_file)
        config.to_yaml(output_path)

        print(f"[green]Configuration saved[/green] {output_path}")

        if template:
            print("[bold]Template configuration generated[/bold]")
            print(f"Edit {output_path} to customize your pipeline")

    except Exception as e:
        print(f"[red]Configuration generation failed[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

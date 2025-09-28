#!/usr/bin/env python3
"""
PEFC CLI - Unified CLI with Typer for pack operations
"""
from __future__ import annotations
import json
from pathlib import Path
import typer
from typing import Optional

from pefc.config.loader import load_config
from pefc.logging import init_logging
from pefc.events import get_event_bus
from pefc.events.subscribers import LoggingSubscriber
from pefc.pipeline.loader import load_pipeline
from pefc.pipeline.core import PipelineRunner
from pefc.pack.verify import verify_zip, print_manifest
from pefc.pack.signing import sign_with_cosign
from pefc.errors import UNEXPECTED_ERROR_EXIT_CODE

app = typer.Typer(add_completion=False, help="PEFC CLI")
pack = typer.Typer(help="Pack operations")
app.add_typer(pack, name="pack")


@app.callback()
def main_cb(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None, "--config", help="Chemin config/pack.yaml"
    ),
    json_logs: Optional[bool] = typer.Option(
        None, "--json-logs/--no-json-logs", help="Force JSON logs"
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Niveau de logs"),
):
    """PEFC CLI - Unified CLI for pack operations."""
    cfg = load_config(path=str(config) if config else "config/pack.yaml")
    init_logging(
        json_mode=bool(
            json_logs if json_logs is not None else getattr(cfg.logging, "json", False)
        )
    )
    import logging

    logging.getLogger().setLevel(log_level.upper())

    # EventBus → LoggingSubscriber global
    get_event_bus().subscribe(
        "*", LoggingSubscriber(logging.getLogger("pefc.events")).handler, priority=-100
    )
    ctx.obj = {"cfg": cfg}


@pack.command("build")
def pack_build(
    ctx: typer.Context,
    pipeline: Optional[Path] = typer.Option(
        None, "--pipeline", help="Descriptor YAML du pipeline"
    ),
    strict: bool = typer.Option(
        False, "--strict/--no-strict", help="Échoue si signature rate"
    ),
    out_dir: Optional[Path] = typer.Option(
        None, "--out-dir", help="Override cfg.pack.out_dir"
    ),
):
    """Build a pack using the specified pipeline."""
    cfg = ctx.obj["cfg"]
    if out_dir:
        cfg.pack.out_dir = str(out_dir)

    pipeline_path = str(pipeline) if pipeline else "config/pipelines/bench_pack.yaml"
    steps = load_pipeline(pipeline_path)
    code = PipelineRunner(cfg, strict_sign=strict).execute(steps)
    raise typer.Exit(code)


@pack.command("verify")
def pack_verify(
    zip_path: Path = typer.Option(..., "--zip", exists=True, readable=True),
    sig_path: Optional[Path] = typer.Option(
        None, "--sig", help="Chemin signature .sig"
    ),
    key_ref: Optional[str] = typer.Option(
        None, "--key", help="Clé/KeyRef pour cosign verify-blob"
    ),
    strict: bool = typer.Option(
        True, "--strict/--no-strict", help="Échoue si merkle/manifest incompatibles"
    ),
):
    """Verify a pack artifact (manifest, merkle, signature)."""
    ok, report = verify_zip(zip_path, sig_path=sig_path, key_ref=key_ref, strict=strict)
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    raise typer.Exit(0 if ok else 1)


@pack.command("manifest")
def pack_manifest(
    zip_path: Path = typer.Option(..., "--zip", exists=True, readable=True),
    out: Optional[Path] = typer.Option(None, "--out"),
    print_: bool = typer.Option(False, "--print", help="Affiche le manifest JSON"),
):
    """Extract or print manifest from a pack artifact."""
    manifest = print_manifest(zip_path)
    if out:
        Path(out).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if print_ or not out:
        typer.echo(json.dumps(manifest, ensure_ascii=False, indent=2))
    raise typer.Exit(0)


@pack.command("sign")
def pack_sign(
    artifact: Path = typer.Option(..., "--in", exists=True, readable=True),
    provider: str = typer.Option("cosign", "--provider"),
    key_ref: Optional[str] = typer.Option(None, "--key"),
):
    """Sign a pack artifact."""
    if provider == "cosign":
        try:
            sig = sign_with_cosign(artifact, key_ref=key_ref)
            typer.echo(str(sig))
            raise typer.Exit(0)
        except Exception as e:
            typer.echo(f"Signature failed: {e}", err=True)
            raise typer.Exit(UNEXPECTED_ERROR_EXIT_CODE)
    else:
        typer.echo("Unknown provider", err=True)
        raise typer.Exit(2)


@app.command("version")
def version_cmd():
    """Print version information."""
    from pefc import __version__

    typer.echo(__version__)


if __name__ == "__main__":
    app()

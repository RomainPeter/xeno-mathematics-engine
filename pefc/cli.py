#!/usr/bin/env python3
"""
PEFC CLI - Configuration and diagnostics
"""
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config.loader import load_config
from .container import ServiceContainer

app = typer.Typer()
console = Console()


@app.command()
def validate(
    config: Path = typer.Option("config/pack.yaml", help="Configuration file path"),
    env: Optional[str] = typer.Option(None, help="Environment profile"),
):
    """Validate configuration file."""
    try:
        cfg = load_config(config, env=env)
        container = ServiceContainer(cfg)
        errors = container.validate()

        if errors:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
        else:
            console.print("[green]Configuration is valid[/green]")
            if cfg._active_env:
                console.print(f"Active environment: {cfg._active_env}")

    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        sys.exit(1)


@app.command()
def show(
    config: Path = typer.Option("config/pack.yaml", help="Configuration file path"),
    env: Optional[str] = typer.Option(None, help="Environment profile"),
    format: str = typer.Option("yaml", help="Output format (json/yaml)"),
):
    """Show configuration."""
    try:
        cfg = load_config(config, env=env)

        if format == "json":
            # Convert to dict and remove private fields
            data = cfg.model_dump()
            data.pop("_base_dir", None)
            data.pop("_active_env", None)
            console.print(json.dumps(data, indent=2, default=str))
        else:
            # Show key configuration values
            table = Table(title="Configuration")
            table.add_column("Section", style="cyan")
            table.add_column("Key", style="magenta")
            table.add_column("Value", style="green")

            # Pack config
            table.add_row("pack", "version", cfg.pack.version)
            table.add_row("pack", "pack_name", cfg.pack.pack_name)
            table.add_row("pack", "out_dir", cfg.pack.out_dir)

            # Logging config
            table.add_row("logging", "level", cfg.logging.level)
            table.add_row("logging", "json", str(cfg.logging.json))

            # Metrics config
            table.add_row("metrics", "sources", str(cfg.metrics.sources))
            table.add_row("metrics", "backend", cfg.metrics.backend)

            # Capabilities
            capability_count = len(cfg.capabilities.registry)
            table.add_row("capabilities", "registry_count", str(capability_count))

            # Pipelines
            pipeline_count = len(cfg.pipelines.defs)
            table.add_row("pipelines", "defs_count", str(pipeline_count))
            table.add_row("pipelines", "default", cfg.pipelines.default)

            if cfg._active_env:
                table.add_row("runtime", "active_env", cfg._active_env)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        sys.exit(1)


@app.command()
def container(
    config: Path = typer.Option("config/pack.yaml", help="Configuration file path"),
    env: Optional[str] = typer.Option(None, help="Environment profile"),
):
    """Diagnose service container."""
    try:
        cfg = load_config(config, env=env)
        container = ServiceContainer(cfg)

        # Check for validation errors
        errors = container.validate()
        if errors:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)

        # Build services
        console.print("[blue]Building services...[/blue]")

        # Event bus
        bus = container.get_event_bus()
        console.print(f"✓ Event bus: {type(bus).__name__}")

        # Logger
        logger = container.get_logger()
        console.print(f"✓ Logger: {logger.name}")

        # Metrics provider
        metrics_provider = container.get_metrics_provider()
        console.print(f"✓ Metrics provider: {type(metrics_provider).__name__}")

        # Capability registry
        registry = container.get_capability_registry()
        handlers = registry.list_handlers()
        console.print(f"✓ Capability registry: {len(handlers)} handlers")

        # Show handlers
        if handlers:
            table = Table(title="Capability Handlers")
            table.add_column("ID", style="cyan")
            table.add_column("Version", style="magenta")
            table.add_column("Provides", style="green")
            table.add_column("Prerequisites", style="yellow")

            for handler in handlers:
                prereq_missing = ", ".join(handler.get("prereq_missing", []))
                table.add_row(
                    handler["id"],
                    handler.get("version", "unknown"),
                    ", ".join(handler.get("provides", [])),
                    prereq_missing or "none",
                )

            console.print(table)

        # Pipelines
        console.print(f"✓ Pipelines: {len(cfg.pipelines.defs)} definitions")

        # Show pipeline steps
        for pipeline_name, pipeline_def in cfg.pipelines.defs.items():
            console.print(f"\n[blue]Pipeline '{pipeline_name}':[/blue]")
            for i, step in enumerate(pipeline_def.steps, 1):
                console.print(f"  {i}. {step.type} ({step.name or 'unnamed'})")

        console.print("\n[green]All services built successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error building container:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()

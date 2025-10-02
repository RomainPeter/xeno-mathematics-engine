"""
Boucle AE (Attribute Exploration) avec timeout et gestion d'incidents.
"""
from __future__ import annotations
import asyncio
import orjson
from pathlib import Path
from xme.orchestrator.state import RunState
from xme.orchestrator.event_bus import EventBus
from xme.engines.ae.context import load_context
from xme.engines.ae.next_closure_stub import enumerate_concepts_stub
from xme.engines.ae.psp_builder import concepts_to_psp
from xme.adapters.logger import log_action
from xme.pcap.store import PCAPStore


class AETimeout(Exception):
    """Exception levée lors d'un timeout AE."""
    pass


async def run_ae(
    context_path: str, 
    state: RunState, 
    bus: EventBus, 
    store: PCAPStore, 
    out_psp: Path
) -> None:
    """
    Exécute la boucle AE avec timeout et gestion d'incidents.
    
    Args:
        context_path: Chemin vers le contexte FCA
        state: État de l'exécution
        bus: Bus d'événements
        store: Store PCAP pour le logging
        out_psp: Chemin de sortie pour le PSP
    """
    async def _task():
        ctx = load_context(context_path)
        concepts = enumerate_concepts_stub(ctx)
        psp = concepts_to_psp(concepts)
        
        out_psp.parent.mkdir(parents=True, exist_ok=True)
        out_psp.write_text(psp.canonical_json())
        
        log_action(store, action="ae_psp_emitted", psp_ref=str(out_psp))
        
        await bus.emit({
            "type": "ae.done", 
            "n_blocks": len(psp.blocks), 
            "n_edges": len(psp.edges)
        })
    
    try:
        await asyncio.wait_for(_task(), timeout=state.budgets.ae_ms/1000.0)
    except asyncio.TimeoutError as e:
        log_action(
            store, 
            action="incident.ae_timeout", 
            level="S0", 
            obligations={"budget_ms": str(state.budgets.ae_ms)}
        )
        raise AETimeout() from e

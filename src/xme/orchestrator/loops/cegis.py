"""
Boucle CEGIS asynchrone avec gestion de budget, timeout et incidents.
"""
from __future__ import annotations
import asyncio
import orjson
from pathlib import Path
from typing import Any, Dict
from xme.orchestrator.state import RunState
from xme.orchestrator.event_bus import EventBus
from xme.engines.cegis.engine import CEGISEngine
from xme.engines.cegis.domains.bitvector import BitvectorDomain, BitvectorState
from xme.adapters.logger import log_action
from xme.pcap.store import PCAPStore


class CEGISTimeout(Exception):
    """Exception levée lors d'un timeout CEGIS."""
    pass


async def run_cegis(
    secret: str,
    max_iters: int,
    state: RunState,
    bus: EventBus,
    store: PCAPStore,
    out_path: Path
) -> None:
    """
    Exécute la boucle CEGIS avec logging PCAP et gestion de timeout.
    
    Args:
        secret: Vecteur de bits secret à synthétiser
        max_iters: Nombre maximum d'itérations
        state: État de l'exécution
        bus: Bus d'événements
        store: Store PCAP pour le logging
        out_path: Chemin de sortie pour le résultat
    """
    async def _task():
        # Initialiser le domaine et le moteur
        domain = BitvectorDomain(secret)
        engine = CEGISEngine(domain)
        
        # Log du début
        log_action(store, action="cegis_start", level="S0", 
                  obligations={"secret_length": str(len(secret)), "max_iters": str(max_iters)})
        
        # Exécuter CEGIS
        initial_state = domain.create_initial_state()
        result = engine.run(max_iters, initial_state)
        
        # Log des itérations
        for i, candidate in enumerate(engine.state.candidates):
            log_action(store, action="cegis_propose", level="S0", 
                      obligations={"iteration": str(i + 1), "candidate": candidate["bits"]})
            
            # Vérification
            verdict, counterexample = domain.verify(candidate)
            if verdict == "ok":
                log_action(store, action="cegis_verify_ok", level="S0", 
                          obligations={"candidate": candidate["bits"]})
                break
            else:
                log_action(store, action="cegis_verify_fail", level="S0", 
                          obligations={"candidate": candidate["bits"], 
                                     "mismatch_positions": str(counterexample["mismatch"])})
                
                if i < len(engine.state.candidates) - 1:  # Pas la dernière itération
                    log_action(store, action="cegis_refine", level="S0", 
                              obligations={"counterexample": str(counterexample)})
        
        # Log de fin
        log_action(store, action="cegis_done", level="S0", 
                  obligations={"result_ok": str(result.ok), "iterations": str(result.iters)})
        
        # Sauvegarder le résultat
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(orjson.dumps(result.to_dict()).decode())
        
        # Émettre l'événement de fin
        await bus.emit({
            "type": "cegis.done", 
            "result_ok": result.ok,
            "iterations": result.iters,
            "candidate": result.candidate
        })
    
    try:
        # Exécuter avec timeout
        timeout_seconds = state.budgets.cegis_ms / 1000.0 if state.budgets.cegis_ms > 0 else 30.0
        await asyncio.wait_for(_task(), timeout=timeout_seconds)
    except asyncio.TimeoutError as e:
        # Log de l'incident de timeout
        log_action(store, action="incident.cegis_timeout", level="S0", 
                  obligations={"budget_ms": str(state.budgets.cegis_ms)})
        raise CEGISTimeout() from e

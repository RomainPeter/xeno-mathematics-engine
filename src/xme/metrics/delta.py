"""
Calcul des métriques de friction δ (adjunction defect).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from xme.engines.cegis.types import CEGISResult
from xme.pcap.store import PCAPStore
from xme.psp.schema import PSP


def compute_delta_ae(psp_before: Dict[str, Any], psp_after_or_checks: Dict[str, Any]) -> float:
    """
    Calcule δ_ae = 1 - (|E_cover_validées| / |E_cover_proposées|) si S1 échoue partiellement.

    Args:
        psp_before: PSP avant vérification
        psp_after_or_checks: PSP après vérification ou résultats de vérification

    Returns:
        δ_ae ∈ [0, 1] où 0 = parfait, 1 = échec total
    """
    try:
        # Charger les PSP
        psp_before_obj = PSP.model_validate(psp_before)
        psp_after_obj = PSP.model_validate(psp_after_or_checks)

        # Compter les arêtes proposées (avant)
        edges_proposed = len(psp_before_obj.edges)

        # Compter les arêtes validées (après)
        edges_validated = len(psp_after_obj.edges)

        if edges_proposed == 0:
            return 0.0  # Aucune arête proposée, pas de friction

        # Calculer δ_ae
        if edges_validated >= edges_proposed:
            return 0.0  # Toutes les arêtes validées, pas de friction
        else:
            delta = 1.0 - (edges_validated / edges_proposed)
            return min(max(delta, 0.0), 1.0)  # Borner entre 0 et 1

    except Exception:
        # En cas d'erreur, considérer comme échec total
        return 1.0


def compute_delta_ae_from_verification(
    psp_data: Dict[str, Any], verification_results: List[Dict[str, Any]]
) -> float:
    """
    Calcule δ_ae basé sur les résultats de vérification S1.

    Args:
        psp_data: Données PSP
        verification_results: Résultats de vérification

    Returns:
        δ_ae ∈ [0, 1]
    """
    try:
        psp = PSP.model_validate(psp_data)
        total_edges = len(psp.edges)

        if total_edges == 0:
            return 0.0

        # Compter les vérifications S1 qui ont échoué
        s1_failures = 0
        s1_total = 0

        for result in verification_results:
            if result.get("level") == "S1":
                s1_total += 1
                if not result.get("ok", False):
                    s1_failures += 1

        if s1_total == 0:
            return 0.0  # Aucune vérification S1

        # δ_ae basé sur le taux d'échec S1
        delta = s1_failures / s1_total
        return min(max(delta, 0.0), 1.0)

    except Exception:
        return 1.0


def compute_delta_cegis(trace: Dict[str, Any]) -> float:
    """
    Calcule δ_cegis = (iters_fail / iters_total) ou 1 si non convergence sous budget.

    Args:
        trace: Trace CEGIS avec résultats

    Returns:
        δ_cegis ∈ [0, 1] où 0 = parfait, 1 = échec total
    """
    try:
        # Extraire les informations de la trace
        iters_total = trace.get("iters", 0)
        converged = trace.get("ok", False)
        max_iter = trace.get("max_iter", 16)

        if iters_total == 0:
            return 1.0  # Aucune itération, échec total

        if converged:
            # Convergence réussie, δ basé sur l'efficacité
            efficiency = 1.0 - (iters_total / max_iter)
            return max(0.0, efficiency)  # Plus c'est efficace, plus δ est faible
        else:
            # Non convergence, δ = 1
            return 1.0

    except Exception:
        return 1.0


def compute_delta_cegis_from_result(cegis_result: CEGISResult, max_iter: int = 16) -> float:
    """
    Calcule δ_cegis à partir d'un résultat CEGIS.

    Args:
        cegis_result: Résultat CEGIS
        max_iter: Nombre maximum d'itérations

    Returns:
        δ_cegis ∈ [0, 1]
    """
    try:
        if cegis_result.iters == 0:
            return 1.0

        if cegis_result.ok:
            # Convergence réussie
            efficiency = 1.0 - (cegis_result.iters / max_iter)
            return max(0.0, efficiency)
        else:
            # Non convergence
            return 1.0

    except Exception:
        return 1.0


def aggregate_run_delta(pcap_path: Path) -> Dict[str, Any]:
    """
    Agrège les δ d'un run PCAP avec moyenne pondérée.

    Args:
        pcap_path: Chemin vers le run PCAP

    Returns:
        Dictionnaire avec delta_run et deltas_by_phase
    """
    try:
        store = PCAPStore(pcap_path)
        entries = list(store.read_all())

        deltas_by_phase = {}
        phase_weights = {}
        phase_durations = {}

        # Analyser les entrées pour extraire les δ
        for entry in entries:
            action = entry.get("action", "")
            deltas = entry.get("deltas", {})
            obligations = entry.get("obligations", {})

            # Extraire les δ des deltas
            for key, value in deltas.items():
                if key.startswith("delta_"):
                    phase = key.replace("delta_", "")
                    if phase not in deltas_by_phase:
                        deltas_by_phase[phase] = []
                    deltas_by_phase[phase].append(float(value))

            # Extraire les δ des obligations
            for key, value in obligations.items():
                if key.startswith("delta_"):
                    phase = key.replace("delta_", "")
                    if phase not in deltas_by_phase:
                        deltas_by_phase[phase] = []
                    deltas_by_phase[phase].append(float(value))

            # Calculer les poids basés sur la durée ou le nombre d'actions
            if action in ["ae_psp_emitted", "cegis_start", "discovery_turn_done"]:
                phase = action.split("_")[0] if "_" in action else "unknown"
                if phase not in phase_weights:
                    phase_weights[phase] = 0
                phase_weights[phase] += 1

        # Calculer les δ moyens par phase
        phase_averages = {}
        for phase, deltas in deltas_by_phase.items():
            if deltas:
                phase_averages[phase] = sum(deltas) / len(deltas)
            else:
                phase_averages[phase] = 0.0

        # Calculer le δ moyen pondéré du run
        if phase_averages and phase_weights:
            total_weight = sum(phase_weights.values())
            if total_weight > 0:
                weighted_sum = sum(
                    phase_averages.get(phase, 0.0) * phase_weights.get(phase, 0)
                    for phase in set(phase_averages.keys()) | set(phase_weights.keys())
                )
                delta_run = weighted_sum / total_weight
            else:
                delta_run = (
                    sum(phase_averages.values()) / len(phase_averages) if phase_averages else 0.0
                )
        else:
            delta_run = 0.0

        return {
            "delta_run": min(max(delta_run, 0.0), 1.0),  # Borner entre 0 et 1
            "deltas_by_phase": phase_averages,
            "phase_weights": phase_weights,
            "total_entries": len(entries),
        }

    except Exception as e:
        return {
            "delta_run": 1.0,  # Échec total en cas d'erreur
            "deltas_by_phase": {},
            "phase_weights": {},
            "total_entries": 0,
            "error": str(e),
        }


def compute_delta_bounds(delta: float) -> float:
    """
    Borne une valeur δ entre 0 et 1.

    Args:
        delta: Valeur δ à borner

    Returns:
        δ ∈ [0, 1]
    """
    return min(max(float(delta), 0.0), 1.0)


def validate_delta(delta: float, name: str = "delta") -> float:
    """
    Valide et borne une valeur δ.

    Args:
        delta: Valeur δ à valider
        name: Nom de la métrique pour les erreurs

    Returns:
        δ ∈ [0, 1]

    Raises:
        ValueError: Si δ n'est pas un nombre valide
    """
    try:
        delta_float = float(delta)
        if not (0.0 <= delta_float <= 1.0):
            return compute_delta_bounds(delta_float)
        return delta_float
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {name} value: {delta}")


def compute_phase_delta(phase_entries: List[Dict[str, Any]], phase_name: str) -> float:
    """
    Calcule le δ pour une phase spécifique.

    Args:
        phase_entries: Entrées PCAP pour la phase
        phase_name: Nom de la phase

    Returns:
        δ de la phase ∈ [0, 1]
    """
    if not phase_entries:
        return 0.0

    deltas = []
    for entry in phase_entries:
        # Extraire les δ des deltas
        entry_deltas = entry.get("deltas", {})
        for key, value in entry_deltas.items():
            if key.startswith("delta_"):
                try:
                    deltas.append(float(value))
                except (ValueError, TypeError):
                    continue

        # Extraire les δ des obligations
        entry_obligations = entry.get("obligations", {})
        for key, value in entry_obligations.items():
            if key.startswith("delta_"):
                try:
                    deltas.append(float(value))
                except (ValueError, TypeError):
                    continue

    if not deltas:
        return 0.0

    # Calculer la moyenne des δ
    avg_delta = sum(deltas) / len(deltas)
    return compute_delta_bounds(avg_delta)

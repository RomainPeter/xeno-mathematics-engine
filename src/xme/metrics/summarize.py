"""
Système de synthèse des métriques et résumés de run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, MutableMapping

import orjson

from xme.metrics.delta import aggregate_run_delta, compute_delta_bounds
from xme.pcap.store import PCAPStore


def summarize_run(pcap_path: Path) -> Dict[str, Any]:
    """
    Synthétise un run PCAP avec comptages, incidents, δ et merkle_root.

    Args:
        pcap_path: Chemin vers le run PCAP

    Returns:
        Dictionnaire de synthèse avec toutes les métriques
    """
    try:
        store = PCAPStore(pcap_path)
        entries = list(store.read_all())

        if not entries:
            return {
                "run_path": str(pcap_path),
                "total_entries": 0,
                "actions": {},
                "incidents": [],
                "deltas": {},
                "merkle_root": None,
                "summary": "Empty run",
            }

        # Compter les actions
        actions: Dict[str, int] = {}
        for entry in entries:
            action = entry.get("action", "unknown")
            actions[action] = actions.get(action, 0) + 1

        # Identifier les incidents (actions d'erreur ou d'échec)
        incidents = []
        for entry in entries:
            action = entry.get("action", "")
            level = entry.get("level", "")
            obligations = entry.get("obligations", {})

            # Détecter les incidents
            is_incident = False
            incident_type = "unknown"

            if "error" in action.lower() or "fail" in action.lower():
                is_incident = True
                incident_type = "error"
            elif "timeout" in action.lower():
                is_incident = True
                incident_type = "timeout"
            elif "incident" in action.lower():
                is_incident = True
                incident_type = "incident"
            elif any(obligations.get(key, "").lower() == "false" for key in obligations.keys()):
                is_incident = True
                incident_type = "verification_failure"

            if is_incident:
                incidents.append(
                    {
                        "timestamp": entry.get("timestamp", ""),
                        "action": action,
                        "level": level,
                        "type": incident_type,
                        "details": {"obligations": obligations, "deltas": entry.get("deltas", {})},
                    }
                )

        # Calculer les δ
        delta_info = aggregate_run_delta(pcap_path)

        # Extraire le merkle_root si disponible
        merkle_root = None
        for entry in entries:
            if "merkle" in entry.get("action", "").lower():
                merkle_root = entry.get("deltas", {}).get("merkle_root")
                if merkle_root:
                    break

        # Calculer les statistiques temporelles
        timestamps = [entry.get("timestamp", "") for entry in entries if entry.get("timestamp")]
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None

        # Calculer les métriques par niveau
        level_stats: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            level = entry.get("level", "unknown")
            if level not in level_stats:
                level_stats[level] = {"count": 0, "actions": set()}
            level_stats[level]["count"] += 1
            level_stats[level]["actions"].add(entry.get("action", ""))

        # Convertir les sets en listes pour la sérialisation JSON
        for level in level_stats:
            level_stats[level]["actions"] = list(level_stats[level]["actions"])

        # Calculer les métriques de performance
        performance_metrics = {
            "total_actions": len(entries),
            "unique_actions": len(set(entry.get("action", "") for entry in entries)),
            "incident_rate": len(incidents) / len(entries) if entries else 0.0,
            "delta_run": delta_info.get("delta_run", 0.0),
            "phases_with_deltas": len(delta_info.get("deltas_by_phase", {})),
        }

        # Créer le résumé
        summary = {
            "run_path": str(pcap_path),
            "total_entries": len(entries),
            "start_time": start_time,
            "end_time": end_time,
            "actions": actions,
            "incidents": incidents,
            "deltas": {
                "delta_run": compute_delta_bounds(delta_info.get("delta_run", 0.0)),
                "deltas_by_phase": delta_info.get("deltas_by_phase", {}),
                "phase_weights": delta_info.get("phase_weights", {}),
            },
            "level_stats": level_stats,
            "performance": performance_metrics,
            "merkle_root": merkle_root,
            "summary": f"Run with {len(entries)} entries, {len(incidents)} incidents, δ={delta_info.get('delta_run', 0.0):.3f}",
        }

        return summary

    except Exception as e:
        return {
            "run_path": str(pcap_path),
            "total_entries": 0,
            "actions": {},
            "incidents": [],
            "deltas": {"delta_run": 1.0, "deltas_by_phase": {}, "phase_weights": {}},
            "merkle_root": None,
            "summary": f"Error processing run: {str(e)}",
            "error": str(e),
        }


def summarize_multiple_runs(pcap_paths: List[Path]) -> Dict[str, Any]:
    """
    Synthétise plusieurs runs PCAP.

    Args:
        pcap_paths: Liste des chemins vers les runs PCAP

    Returns:
        Dictionnaire de synthèse agrégée
    """
    summaries = []
    total_entries = 0
    total_incidents = 0
    all_actions: Dict[str, int] = {}
    all_deltas = []

    for pcap_path in pcap_paths:
        summary = summarize_run(pcap_path)
        summaries.append(summary)

        total_entries += summary.get("total_entries", 0)
        total_incidents += len(summary.get("incidents", []))

        # Agréger les actions
        for action, count in summary.get("actions", {}).items():
            all_actions[action] = all_actions.get(action, 0) + count

        # Agréger les δ
        delta_run = summary.get("deltas", {}).get("delta_run", 0.0)
        all_deltas.append(delta_run)

    # Calculer les métriques agrégées
    avg_delta = sum(all_deltas) / len(all_deltas) if all_deltas else 0.0
    min_delta = min(all_deltas) if all_deltas else 0.0
    max_delta = max(all_deltas) if all_deltas else 0.0

    return {
        "runs_processed": len(pcap_paths),
        "total_entries": total_entries,
        "total_incidents": total_incidents,
        "actions": all_actions,
        "deltas": {
            "average": compute_delta_bounds(avg_delta),
            "minimum": compute_delta_bounds(min_delta),
            "maximum": compute_delta_bounds(max_delta),
            "all_values": all_deltas,
        },
        "summaries": summaries,
        "summary": f"Processed {len(pcap_paths)} runs, {total_entries} total entries, avg δ={avg_delta:.3f}",
    }


def export_summary_json(summary: Dict[str, Any], output_path: Path) -> None:
    """
    Exporte un résumé en JSON.

    Args:
        summary: Résumé à exporter
        output_path: Chemin de sortie
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(orjson.dumps(summary, option=orjson.OPT_INDENT_2))


def load_summary_json(input_path: Path) -> Dict[str, Any]:
    """
    Charge un résumé depuis un fichier JSON.

    Args:
        input_path: Chemin d'entrée

    Returns:
        Résumé chargé
    """
    with open(input_path, "rb") as f:
        return orjson.loads(f.read())


def compare_summaries(summary1: Dict[str, Any], summary2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare deux résumés et retourne les différences.

    Args:
        summary1: Premier résumé
        summary2: Deuxième résumé

    Returns:
        Dictionnaire de comparaison
    """
    delta1 = summary1.get("deltas", {}).get("delta_run", 0.0)
    delta2 = summary2.get("deltas", {}).get("delta_run", 0.0)

    entries1 = summary1.get("total_entries", 0)
    entries2 = summary2.get("total_entries", 0)

    incidents1 = len(summary1.get("incidents", []))
    incidents2 = len(summary2.get("incidents", []))

    return {
        "delta_comparison": {
            "summary1": delta1,
            "summary2": delta2,
            "difference": delta2 - delta1,
            "improvement": delta1 > delta2,
        },
        "entries_comparison": {
            "summary1": entries1,
            "summary2": entries2,
            "difference": entries2 - entries1,
        },
        "incidents_comparison": {
            "summary1": incidents1,
            "summary2": incidents2,
            "difference": incidents2 - incidents1,
        },
        "summary": f"δ: {delta1:.3f} → {delta2:.3f} ({'improved' if delta1 > delta2 else 'degraded'})",
    }

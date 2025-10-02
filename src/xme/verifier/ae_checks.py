"""
Vérifications AE S0/S1.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from xme.engines.ae.context import FCAContext
from xme.engines.ae.next_closure import enumerate_concepts


def check_ae_intents_unique(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie que les intents sont uniques.

    Args:
        payload: Données AE à vérifier (contexte FCA)

    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le contexte FCA
        if isinstance(payload, dict) and "attributes" in payload and "objects" in payload:
            context = FCAContext.model_validate(payload)
        else:
            return False, {
                "message": "Invalid FCA context format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict",
            }

        # Énumérer les concepts
        concepts = enumerate_concepts(context)

        # Extraire les intents
        intents = [intent for (_, intent) in concepts]

        # Vérifier l'unicité
        unique_intents = set()
        duplicates = []

        for i, intent in enumerate(intents):
            intent_tuple = tuple(sorted(intent))
            if intent_tuple in unique_intents:
                duplicates.append({"index": i, "intent": sorted(list(intent))})
            else:
                unique_intents.add(intent_tuple)

        if duplicates:
            return False, {
                "message": "Duplicate intents found",
                "duplicates": duplicates,
                "n_concepts": len(concepts),
                "n_unique_intents": len(unique_intents),
            }

        return True, {
            "message": "All intents are unique",
            "n_concepts": len(concepts),
            "n_intents": len(intents),
        }

    except Exception as e:
        return False, {
            "message": f"Error checking AE intents uniqueness: {str(e)}",
            "error": str(e),
        }


def check_ae_next_closure_stable(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S1: Vérifie que l'ordre Next-Closure est stable (idempotence sur double run).

    Args:
        payload: Données AE à vérifier (contexte FCA)

    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le contexte FCA
        if isinstance(payload, dict) and "attributes" in payload and "objects" in payload:
            context = FCAContext.model_validate(payload)
        else:
            return False, {
                "message": "Invalid FCA context format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict",
            }

        # Exécuter Next-Closure deux fois
        concepts1 = enumerate_concepts(context)
        concepts2 = enumerate_concepts(context)

        # Comparer les résultats
        if len(concepts1) != len(concepts2):
            return False, {
                "message": "Next-Closure is not stable: different number of concepts",
                "first_run": len(concepts1),
                "second_run": len(concepts2),
            }

        # Comparer les intents
        intents1 = [sorted(list(intent)) for (_, intent) in concepts1]
        intents2 = [sorted(list(intent)) for (_, intent) in concepts2]

        if intents1 != intents2:
            return False, {
                "message": "Next-Closure is not stable: different intents",
                "n_concepts": len(concepts1),
                "first_run_intents": intents1,
                "second_run_intents": intents2,
            }

        # Comparer les extents
        extents1 = [sorted(list(extent)) for (extent, _) in concepts1]
        extents2 = [sorted(list(extent)) for (extent, _) in concepts2]

        if extents1 != extents2:
            return False, {
                "message": "Next-Closure is not stable: different extents",
                "n_concepts": len(concepts1),
                "first_run_extents": extents1,
                "second_run_extents": extents2,
            }

        return True, {
            "message": "Next-Closure is stable (idempotent)",
            "n_concepts": len(concepts1),
            "n_attributes": len(context.attributes),
            "n_objects": len(context.objects),
        }

    except Exception as e:
        return False, {
            "message": f"Error checking AE Next-Closure stability: {str(e)}",
            "error": str(e),
        }


def check_ae_concepts_completeness(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S1: Vérifie que tous les concepts sont trouvés (completude).

    Args:
        payload: Données AE à vérifier (contexte FCA)

    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le contexte FCA
        if isinstance(payload, dict) and "attributes" in payload and "objects" in payload:
            context = FCAContext.model_validate(payload)
        else:
            return False, {
                "message": "Invalid FCA context format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict",
            }

        # Énumérer les concepts
        concepts = enumerate_concepts(context)

        # Vérifier que le nombre de concepts est raisonnable
        # Pour un contexte avec n attributs, le nombre maximum de concepts est 2^n
        max_concepts = 2 ** len(context.attributes)
        actual_concepts = len(concepts)

        if actual_concepts > max_concepts:
            return False, {
                "message": "Too many concepts found (impossible)",
                "actual_concepts": actual_concepts,
                "max_possible": max_concepts,
                "n_attributes": len(context.attributes),
            }

        # Vérifier qu'il y a au moins le concept vide (intent vide)
        empty_intent_found = any(len(intent) == 0 for (_, intent) in concepts)
        if not empty_intent_found:
            return False, {
                "message": "Empty intent concept not found",
                "n_concepts": actual_concepts,
            }

        # Vérifier qu'il y a au moins le concept universel (intent avec tous les attributs)
        all_attrs_intent_found = any(
            len(intent) == len(context.attributes) for (_, intent) in concepts
        )
        if not all_attrs_intent_found:
            return False, {
                "message": "Universal intent concept not found",
                "n_concepts": actual_concepts,
                "n_attributes": len(context.attributes),
            }

        return True, {
            "message": "AE concepts are complete",
            "n_concepts": actual_concepts,
            "n_attributes": len(context.attributes),
            "n_objects": len(context.objects),
            "max_possible": max_concepts,
        }

    except Exception as e:
        return False, {
            "message": f"Error checking AE concepts completeness: {str(e)}",
            "error": str(e),
        }


def get_ae_obligations() -> List[Tuple[str, str, callable, str]]:
    """
    Retourne toutes les obligations AE.

    Returns:
        Liste des obligations (id, level, check_func, description)
    """
    return [
        ("ae_intents_unique", "S0", check_ae_intents_unique, "AE intents must be unique"),
        (
            "ae_next_closure_stable",
            "S1",
            check_ae_next_closure_stable,
            "AE Next-Closure must be stable (idempotent)",
        ),
        ("ae_concepts_complete", "S1", check_ae_concepts_completeness, "AE must find all concepts"),
    ]

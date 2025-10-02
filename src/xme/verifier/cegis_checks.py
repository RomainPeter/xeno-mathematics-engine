"""
Vérifications CEGIS S0.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List
from xme.engines.cegis.types import CEGISResult


def check_cegis_iterations_limit(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie que le nombre d'itérations est dans la limite.
    
    Args:
        payload: Données CEGIS à vérifier
        
    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le résultat CEGIS
        if isinstance(payload, dict) and "iters" in payload:
            result = CEGISResult.model_validate(payload)
        else:
            return False, {
                "message": "Invalid CEGIS result format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict"
            }
        
        # Vérifier que le nombre d'itérations est raisonnable
        max_iter = payload.get("max_iter", 16)  # Limite par défaut
        if result.iters > max_iter:
            return False, {
                "message": "CEGIS exceeded iteration limit",
                "actual_iters": result.iters,
                "max_iter": max_iter,
                "converged": result.ok
            }
        
        return True, {
            "message": "CEGIS iterations within limit",
            "iters": result.iters,
            "max_iter": max_iter,
            "converged": result.ok
        }
        
    except Exception as e:
        return False, {
            "message": f"Error checking CEGIS iterations: {str(e)}",
            "error": str(e)
        }


def check_cegis_secret_match(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie que le candidat final correspond au secret (si fourni).
    
    Args:
        payload: Données CEGIS à vérifier
        
    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le résultat CEGIS
        if isinstance(payload, dict) and "candidate_final" in payload:
            result = CEGISResult.model_validate(payload)
        else:
            return False, {
                "message": "Invalid CEGIS result format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict"
            }
        
        # Vérifier si un secret est fourni
        expected_secret = payload.get("secret")
        if expected_secret is None:
            return True, {
                "message": "No secret provided for verification",
                "converged": result.ok,
                "candidate_final": result.candidate_final
            }
        
        # Vérifier que le candidat final correspond au secret
        if result.candidate_final == expected_secret:
            return True, {
                "message": "CEGIS candidate matches expected secret",
                "secret": expected_secret,
                "candidate_final": result.candidate_final,
                "converged": result.ok
            }
        else:
            return False, {
                "message": "CEGIS candidate does not match expected secret",
                "expected_secret": expected_secret,
                "actual_candidate": result.candidate_final,
                "converged": result.ok
            }
        
    except Exception as e:
        return False, {
            "message": f"Error checking CEGIS secret match: {str(e)}",
            "error": str(e)
        }


def check_cegis_convergence(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    S0: Vérifie que CEGIS a convergé correctement.
    
    Args:
        payload: Données CEGIS à vérifier
        
    Returns:
        Tuple (ok, details)
    """
    try:
        # Charger le résultat CEGIS
        if isinstance(payload, dict) and "ok" in payload:
            result = CEGISResult.model_validate(payload)
        else:
            return False, {
                "message": "Invalid CEGIS result format",
                "payload_keys": list(payload.keys()) if isinstance(payload, dict) else "not_dict"
            }
        
        # Vérifier la convergence
        if result.ok:
            return True, {
                "message": "CEGIS converged successfully",
                "iters": result.iters,
                "candidate_final": result.candidate_final
            }
        else:
            return False, {
                "message": "CEGIS did not converge",
                "iters": result.iters,
                "candidate_final": result.candidate_final
            }
        
    except Exception as e:
        return False, {
            "message": f"Error checking CEGIS convergence: {str(e)}",
            "error": str(e)
        }


def get_cegis_obligations() -> List[Tuple[str, str, callable, str]]:
    """
    Retourne toutes les obligations CEGIS.
    
    Returns:
        Liste des obligations (id, level, check_func, description)
    """
    return [
        ("cegis_iterations_limit", "S0", check_cegis_iterations_limit, "CEGIS iterations must be within limit"),
        ("cegis_secret_match", "S0", check_cegis_secret_match, "CEGIS candidate must match expected secret"),
        ("cegis_convergence", "S0", check_cegis_convergence, "CEGIS must converge successfully")
    ]

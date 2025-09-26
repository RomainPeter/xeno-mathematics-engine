"""
Métriques δ (écart entre intention et résultat).
Combinaison pondérée: violations de K, Jaccard H/E/K, divergence AST (LibCST).
"""

from typing import List, Dict, Set
import libcst as cst
import os
from .schemas import DeltaMetrics


def jaccard(a: Set[str], b: Set[str]) -> float:
    """Calcule la distance de Jaccard entre deux sets."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    return 1 - (len(a & b) / len(a | b))


def ast_divergence(paths: List[str], before_dir: str, after_dir: str) -> float:
    """
    Calcule la divergence AST entre deux répertoires.
    Utilise LibCST pour analyser les différences.
    """
    def dump_ast(path: str) -> str:
        """Dump l'AST d'un fichier Python."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            module = cst.parse_module(content)
            return module.code
        except Exception:
            return ""
    
    diffs = []
    for p in paths:
        pb = os.path.join(before_dir, p)
        pa = os.path.join(after_dir, p)
        
        if os.path.exists(pb) and os.path.exists(pa):
            sb = dump_ast(pb)
            sa = dump_ast(pa)
            
            if sb and sa:
                # Calculer la différence normalisée
                diff_ratio = abs(len(sa) - len(sb)) / max(1, len(sb))
                diffs.append(diff_ratio)
    
    return sum(diffs) / len(diffs) if diffs else 0.0


def compute_delta(H_before: List[str], H_after: List[str],
                  E_before: List[str], E_after: List[str],
                  K_before: List[str], K_after: List[str],
                  changed_paths: List[str], before_dir: str, after_dir: str,
                  violations: int, w: tuple = (0.2, 0.2, 0.2, 0.4)) -> DeltaMetrics:
    """
    Calcule la métrique δ complète.
    
    Args:
        H_before/after: Hypothèses avant/après
        E_before/after: Évidences avant/après
        K_before/after: Obligations avant/après
        changed_paths: Chemins des fichiers modifiés
        before_dir/after_dir: Répertoires avant/après
        violations: Nombre de violations d'obligations
        w: Poids pour les composants (dH, dE, dK, dAST)
    
    Returns:
        DeltaMetrics: Métriques δ complètes
    """
    # Distances de Jaccard
    dH = jaccard(set(H_before), set(H_after))
    dE = jaccard(set(E_before), set(E_after))
    dK = jaccard(set(K_before), set(K_after))
    
    # Divergence AST
    dAST = ast_divergence(changed_paths, before_dir, after_dir)
    
    # Pénalité pour violations
    violations_penalty = min(0.5, 0.1 * violations)
    
    # Delta total pondéré
    delta_total = min(1.0, w[0] * dH + w[1] * dE + w[2] * dK + w[3] * dAST + violations_penalty)
    
    return DeltaMetrics(
        dH=dH,
        dE=dE,
        dK=dK,
        dAST=dAST,
        violations_penalty=violations_penalty,
        delta_total=delta_total
    )


def compute_simple_delta(before_state: Dict[str, Any], after_state: Dict[str, Any],
                        violations: int = 0) -> float:
    """
    Version simplifiée du calcul de delta.
    Utile pour les cas où l'analyse AST n'est pas disponible.
    """
    # Distance basique sur les clés
    before_keys = set(before_state.keys())
    after_keys = set(after_state.keys())
    
    key_distance = jaccard(before_keys, after_keys)
    
    # Pénalité pour violations
    violations_penalty = min(0.3, 0.05 * violations)
    
    return min(1.0, key_distance + violations_penalty)


def analyze_delta_trend(deltas: List[float]) -> Dict[str, Any]:
    """
    Analyse la tendance des deltas.
    Utile pour détecter les patterns d'amélioration/dégradation.
    """
    if not deltas:
        return {"trend": "unknown", "average": 0.0, "volatility": 0.0}
    
    avg_delta = sum(deltas) / len(deltas)
    
    # Calculer la volatilité (écart-type)
    variance = sum((d - avg_delta) ** 2 for d in deltas) / len(deltas)
    volatility = variance ** 0.5
    
    # Déterminer la tendance
    if len(deltas) >= 2:
        recent_trend = deltas[-1] - deltas[-2]
        if recent_trend > 0.1:
            trend = "increasing"
        elif recent_trend < -0.1:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        "trend": trend,
        "average": avg_delta,
        "volatility": volatility,
        "count": len(deltas),
        "latest": deltas[-1] if deltas else 0.0
    }
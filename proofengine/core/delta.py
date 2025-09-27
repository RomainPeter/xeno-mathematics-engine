"""Delta metrics utilities to quantify divergence between states."""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence

from .schemas import DeltaMetrics, XState


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / float(len(set_a | set_b))


def jaccard_distance(a: Iterable[str], b: Iterable[str]) -> float:
    return 1.0 - jaccard_similarity(a, b)


def edit_distance(seq1: Sequence[str], seq2: Sequence[str]) -> int:
    if seq1 == seq2:
        return 0
    if not seq1:
        return len(seq2)
    if not seq2:
        return len(seq1)

    dp = [[0] * (len(seq2) + 1) for _ in range(len(seq1) + 1)]
    for i in range(len(seq1) + 1):
        dp[i][0] = i
    for j in range(len(seq2) + 1):
        dp[0][j] = j

    for i in range(1, len(seq1) + 1):
        for j in range(1, len(seq2) + 1):
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    return dp[-1][-1]


def compute_delta(
    H_before: Iterable[str],
    H_after: Iterable[str],
    E_before: Iterable[str],
    E_after: Iterable[str],
    K_before: Iterable[str],
    K_after: Iterable[str],
    changed_paths: Iterable[str] | None = None,
    before_dir: str | None = None,
    after_dir: str | None = None,
    violations: int = 0,
    weights: Sequence[float] = (0.2, 0.2, 0.2, 0.4),
) -> DeltaMetrics:
    dH = jaccard_distance(H_before, H_after)
    dE = jaccard_distance(E_before, E_after)
    dK = jaccard_distance(K_before, K_after)

    changed_count = len(list(changed_paths or []))
    dAST = min(1.0, 0.1 * changed_count)

    penalty = min(1.0, 0.1 * violations)
    delta_total = min(
        1.0,
        weights[0] * dH
        + weights[1] * dE
        + weights[2] * dK
        + weights[3] * dAST
        + penalty,
    )

    return DeltaMetrics(
        dH=dH,
        dE=dE,
        dK=dK,
        dAST=dAST,
        violations_penalty=penalty,
        delta_total=delta_total,
    )


class DeltaCalculator:
    """Helper exposing richer delta computations for planners and reports."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights: Dict[str, float] = weights or {
            "H": 0.25,
            "E": 0.25,
            "K": 0.25,
            "AST": 0.25,
        }

    def calculate_delta(
        self,
        before: XState,
        after: XState,
        changed_paths: Iterable[str] | None = None,
        violations: int = 0,
    ) -> Dict[str, float]:
        metrics = compute_delta(
            before.H,
            after.H,
            before.E,
            after.E,
            before.K,
            after.K,
            changed_paths=changed_paths,
            weights=(
                self.weights["H"],
                self.weights["E"],
                self.weights["K"],
                self.weights["AST"],
            ),
            violations=violations,
        )
        return metrics.to_dict()

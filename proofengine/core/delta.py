from typing import List
import os

def jaccard(a: set, b: set) -> float:
    if not a and not b: 
        return 0.0
    return 1 - (len(a & b) / max(1, len(a | b)))

def ast_divergence(paths: List[str], before_dir: str, after_dir: str) -> float:
    diffs = []
    for p in paths:
        pb = os.path.join(before_dir, p)
        pa = os.path.join(after_dir, p)
        if os.path.exists(pb) and os.path.exists(pa):
            try:
                with open(pb, "r", encoding="utf-8") as f: 
                    sb = f.read()
                with open(pa, "r", encoding="utf-8") as f: 
                    sa = f.read()
                diffs.append(abs(len(sa) - len(sb)) / max(1, len(sb)))
            except Exception:
                pass
    return sum(diffs) / len(diffs) if diffs else 0.0

def compute_delta(Hb, Ha, Eb, Ea, Kb, Ka, changed_paths: List[str], before_dir: str, after_dir: str, violations: int, w=(0.2, 0.2, 0.2, 0.4)) -> float:
    dH = jaccard(set(Hb), set(Ha))
    dE = jaccard(set(Eb), set(Ea))
    dK = jaccard(set(Kb), set(Ka))
    dAST = ast_divergence(changed_paths, before_dir, after_dir)
    base = w[0] * dH + w[1] * dE + w[2] * dK + w[3] * dAST
    penalty = 0.1 * violations
    return min(1.0, base + penalty)

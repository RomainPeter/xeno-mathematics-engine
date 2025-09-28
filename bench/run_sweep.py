#!/usr/bin/env python3
import json
import itertools
import random
from pathlib import Path


def run_once(lmbda, alpha):
    # Stub: brancher votre policy IDS/CVaR réelle ici
    random.seed(42)
    cov = 0.18 + 0.05 * (1 if lmbda >= 0.6 else 0) + 0.02 * (1 if alpha >= 0.9 else 0)
    nov = 0.19 + 0.03 * (1 if lmbda >= 0.6 else 0)
    cost = 1000 - 50 * (1 if alpha >= 0.9 else 0)
    return {
        "coverage_gain": round(cov, 3),
        "novelty_avg": round(nov, 3),
        "audit_cost_ms": cost,
    }


grid = {"lambda": [0.3, 0.6, 1.0], "alpha": [0.85, 0.9, 0.95]}
results = []
for lmbda, alpha in itertools.product(grid["lambda"], grid["alpha"]):
    r = run_once(lmbda, alpha)
    r.update({"lambda": lmbda, "alpha": alpha})
    results.append(r)
best = max(
    results, key=lambda r: (r["coverage_gain"], r["novelty_avg"], -r["audit_cost_ms"])
)
Path("out").mkdir(parents=True, exist_ok=True)
with open("out/sweep_ids_cvar.json", "w") as f:
    json.dump({"grid": grid, "results": results, "best": best}, f, indent=2)
# Écrit DomainSpec defaults
ds = {"ids": {"lambda": best["lambda"]}, "risk_policy": {"cvar_alpha": best["alpha"]}}
with open("schemas/examples/regtech_domain_spec.overrides.json", "w") as f:
    json.dump(ds, f, indent=2)
print("Sweep complete. Best:", best)

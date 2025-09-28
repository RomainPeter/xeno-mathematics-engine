#!/usr/bin/env python3
import json
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "out/metrics.json"
with open(p) as f:
    m = json.load(f)
cov = m.get("coverage", {}).get("coverage_gain", 0)
nov = m.get("novelty", {}).get("avg", 0)
inc = sum((m.get("incidents", {}).get("counts_by_reason", {}) or {}).values())
# Seuils v0.1
want_cov = 0.20
want_nov = 0.20
max_inc = 999999  # on n'échoue pas sur incidents
ok = True
msgs = []
if cov < want_cov:
    ok = False
    msgs.append(f"coverage_gain {cov:.3f} < {want_cov:.3f}")
if nov < want_nov:
    ok = False
    msgs.append(f"novelty.avg {nov:.3f} < {want_nov:.3f}")
print("Gate summary:", {"coverage_gain": cov, "novelty_avg": nov, "incidents": inc})
if not ok:
    sys.stderr.write("Gate failed: " + "; ".join(msgs) + "\n")
    sys.exit(1)

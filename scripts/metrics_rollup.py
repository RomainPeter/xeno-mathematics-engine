import sys
import json
import os
import glob
import numpy as np
from scipy.stats import pearsonr


def load_metrics(root):
    files = glob.glob(os.path.join(root, "**", "metrics.json"), recursive=True)
    data = []
    for f in files:
        try:
            with open(f) as fh:
                m = json.load(fh)
                data.append(m)
        except Exception as e:
            import logging
            logging.warning(f"Failed to load metrics from {fp}: {e}")
    return data


def corr_delta_incidents(data):
    xs, ys = [], []
    for m in data:
        d = m.get("delta", {}).get("local")
        inc = m.get("incidents", {}).get("total")
        if d is not None and inc is not None:
            xs.append(d)
            ys.append(inc)
    if len(xs) >= 2:
        r, _ = pearsonr(xs, ys)
        return float(r)
    return None


def rollup(data):
    def agg(path, default=None, fn=np.mean):
        vals = []
        for m in data:
            v = m
            for k in path:
                v = v.get(k, {})
            if isinstance(v, (int, float)):
                vals.append(v)
        return float(fn(vals)) if vals else default

    out = {
        "coverage_gain_avg": agg(["coverage", "coverage_gain"]),
        "novelty_avg": agg(["novelty", "avg"]),
        "mdl_compression_avg": agg(["mdl_proxy", "compression"]),
        "delta_local_avg": agg(["delta", "local"]),
        "audit_cost_ms_avg": agg(["audit_cost", "simulated_ms"]),
        "incidents_avg": agg(["incidents", "total"]),
        "delta_incidents_corr": corr_delta_incidents(data),
    }
    return out


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "out/"
    outp = sys.argv[2] if len(sys.argv) > 2 else "rollup/metrics-weekly.json"
    data = load_metrics(root)
    r = rollup(data)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as f:
        json.dump(r, f, indent=2)
    print(json.dumps(r))

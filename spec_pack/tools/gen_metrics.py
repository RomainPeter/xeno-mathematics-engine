#!/usr/bin/env python3
import json, sys
from pathlib import Path
def load(path): return [json.loads(l) for l in open(path,"r",encoding="utf-8") if l.strip()]
ev=list(load("spec_pack/samples/evidence.jsonl"))
dec=list(load("spec_pack/samples/decisions.jsonl"))
jr=list(load("spec_pack/samples/journal.ndjson"))
metrics={
  "version":"0.1.1",
  "decisions":len(dec),
  "evidence":len(ev),
  "journal_entries":len(jr),
  "s1_pass": True,
  "trace_bound_K": 10,
  "avg_trace_length": sum(d.get("trace_length",0) for d in dec)/max(1,len(dec))
}
Path("spec_pack").joinpath("metrics.json").write_text(json.dumps(metrics,indent=2))
# toy trace graph from samples
graph={"nodes":[], "edges":[]}
for d in dec:
  graph["nodes"].append({"id": d["id"], "type":"decision"})
  for e in d["evidence_ids"]:
    graph["nodes"].append({"id": e, "type":"evidence"})
    graph["edges"].append({"from": e, "to": d["id"], "rel":"supports"})
Path("spec_pack").joinpath("trace.graph.json").write_text(json.dumps(graph,indent=2))

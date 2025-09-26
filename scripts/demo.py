import os, json, time, shutil
from dotenv import load_dotenv
from proofengine.core.schemas import XState, PCAP, VJustification
from proofengine.core.pcap import write_pcap, now_iso, merkle_of
from proofengine.core.delta import compute_delta
from proofengine.planner.meta import propose_plan
from proofengine.generator.stochastic import propose_actions
from proofengine.controller.obligations import ensure_tools, evaluate_all
from proofengine.controller.patch import Workspace

def jdump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def main():
    load_dotenv()
    ensure_tools()
    case_id = "demo_case"
    X = XState(H=[f"goal:{case_id}"],
               E=[],
               K=["tests_ok", "lint_ok", "types_ok", "security_ok", "complexity_ok", "docstring_ok"],
               A=[],
               Sigma={"seed": 123})
    plan = propose_plan(f"Improve {case_id} under K", "repo: toy", json.dumps(X.K), "[]")
    p_plan = PCAP(ts=now_iso(), operator="plan", case_id=case_id,
                  pre={"H": X.H, "K": X.K}, post={"plan": plan["plan"]},
                  obligations=X.K, justification=VJustification(time_ms=plan["llm_meta"]["latency_ms"]),
                  proof_state_hash=merkle_of({"H": X.H, "K": X.K}), toolchain={"python": "3.11"})
    write_pcap(p_plan)
    variants = propose_actions(case_id, "toy repo", json.dumps(X.K), k=3)
    all_failed = True
    for v in variants:
        ws = Workspace()
        ok_apply = ws.apply_unified_diff(v["proposal"].get("patch_unified", ""))
        if not ok_apply:
            ws.cleanup()
            continue
        verdicts = evaluate_all(ws.work_dir)
        violations = sum(1 for k, ok in verdicts.items() if not ok)
        delta = compute_delta(X.H, X.H, X.E, X.E, X.K, X.K,
                              changed_paths=["src/utils.py"], before_dir="demo_repo", after_dir=ws.work_dir,
                              violations=violations)
        p_verify = PCAP(ts=now_iso(), operator="verify", case_id=case_id,
                        pre={"verdicts": verdicts}, post={"delta": delta},
                        obligations=list(verdicts.keys()),
                        justification=VJustification(time_ms=0, backtracks=0, audit_cost_ms=0),
                        proof_state_hash=merkle_of(verdicts), toolchain={"python": "3.11"},
                        verdict="pass" if violations == 0 else "fail", llm_meta=v["llm_meta"])
        write_pcap(p_verify)
        if violations == 0:
            all_failed = False
            # promote workspace as new demo_repo state (optional)
            shutil.rmtree("demo_repo", ignore_errors=True)
            shutil.copytree(ws.work_dir, "demo_repo")
            ws.cleanup()
            break
        ws.cleanup()
    if all_failed:
        p_rb = PCAP(ts=now_iso(), operator="rollback", case_id=case_id,
                    pre={}, post={"reason": "all variants failed"}, obligations=X.K,
                    justification=VJustification(time_ms=0, backtracks=1),
                    proof_state_hash=merkle_of({"fail": True}), toolchain={"python": "3.11"}, verdict="fail")
        write_pcap(p_rb)
        # replan once with stricter K (example antifragility: add rule)
        X.K.append("no_regex_backtracking")
        plan2 = propose_plan(f"Replan {case_id}", "repo: toy", json.dumps(X.K), "[]")
        p_replan = PCAP(ts=now_iso(), operator="replan", case_id=case_id,
                        pre={"K_prev": X.K[:-1]}, post={"K_new": X.K, "plan": plan2["plan"]},
                        obligations=X.K, justification=VJustification(time_ms=plan2["llm_meta"]["latency_ms"]),
                        proof_state_hash=merkle_of({"K": X.K}), toolchain={"python": "3.11"}, verdict="fail")
        write_pcap(p_replan)
    # write simple run summary
    jdump("out/metrics/summary.json", {"time": time.time(), "all_failed": all_failed})

if __name__ == "__main__":
    main()
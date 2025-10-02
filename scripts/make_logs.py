#!/usr/bin/env python3
import datetime
import glob
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

OUT_DIR = Path("out")
PCAP_DIR = OUT_DIR / "pcap"
AUDIT_DIR = OUT_DIR / "audit"
METRICS_DIR = OUT_DIR / "metrics"
LOGS_MD = Path("LOGS.md")
SUMMARY_JSON = OUT_DIR / "metrics" / "summary.json"


def load_json(fp):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        import logging

        logging.warning(f"Failed to load JSON from {fp}: {e}")
        return None


def git_commit():
    try:
        h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
        tag = subprocess.check_output(["git", "describe", "--tags", "--always"], text=True).strip()
        return h, tag
    except Exception as e:
        import logging

        logging.warning(f"Failed to get git info: {e}")
        return None, None


def compute_cache_stats():
    cache_dir = Path("proofengine/out/llm_cache")
    if not cache_dir.exists():
        return {"cache_files": 0, "approx_size_kb": 0}
    files = list(cache_dir.glob("*.json"))
    size = sum(f.stat().st_size for f in files) // 1024
    return {"cache_files": len(files), "approx_size_kb": int(size)}


def main():
    os.makedirs(METRICS_DIR, exist_ok=True)
    # Load PCAPs
    pcap_files = sorted(glob.glob(str(PCAP_DIR / "*.json")))
    pcap_entries = [load_json(fp) for fp in pcap_files]
    pcap_entries = [e for e in pcap_entries if e]

    # Load attestation or compute quick digest
    att = load_json(AUDIT_DIR / "attestation.json")
    if not att:
        digest = hashlib.sha256(
            json.dumps([e.get("operator") for e in pcap_entries], sort_keys=True).encode()
        ).hexdigest()
        att = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "pcap_count": len(pcap_entries),
            "digest": digest,
            "verdicts": [],
        }

    # Collect high-level info
    commit, tag = git_commit()
    cache_stats = compute_cache_stats()
    os_info = f"{platform.system()} {platform.release()} | Python {platform.python_version()}"
    model_id = os.getenv("OPENROUTER_MODEL", "unknown-model")

    # Simple metrics if present
    summary = load_json(SUMMARY_JSON) or {}
    replan_count = sum(1 for e in pcap_entries if e.get("operator") == "replan")
    incidents = [e for e in pcap_entries if e.get("operator") in ("incident", "rollback")]
    verifies = [e for e in pcap_entries if e.get("operator") == "verify"]
    passes = sum(1 for e in verifies if e.get("verdict") == "pass")
    fails = sum(1 for e in verifies if e.get("verdict") == "fail")
    delta_vals = []
    for e in verifies:
        try:
            delta_vals.append(float(e.get("post", {}).get("delta", 0)))
        except Exception as e:
            import logging

            logging.warning(f"Failed to parse delta value: {e}")
    delta_mean = round(sum(delta_vals) / len(delta_vals), 3) if delta_vals else None

    # Build sections
    lines = []
    lines.append("# ProofEngine – LOGS.md")
    lines.append("")
    lines.append("## Run metadata")
    lines.append(f"- Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
    lines.append(f"- Commit: {commit or 'n/a'} | Tag: {tag or 'n/a'}")
    lines.append(f"- OS/Python: {os_info}")
    lines.append(f"- Model: {model_id}")
    lines.append(f"- PCAP files: {len(pcap_entries)} | Digest: {att.get('digest')}")
    lines.append(
        f"- Cache: {cache_stats['cache_files']} files (~{cache_stats['approx_size_kb']} KB)"
    )
    lines.append("")

    lines.append("## Commands & expected outcomes")
    lines.append("1) make verify → ping + JSON strict OK")
    lines.append("2) make demo → PCAP plan/verify/(incident|replan|success)")
    lines.append("3) make audit-pack → out/audit/attestation.json")
    lines.append("4) make logs → this file (LOGS.md)")
    lines.append("")

    lines.append("## PCAP timeline (operator → verdict)")
    for fp, e in zip(pcap_files, pcap_entries):
        op = e.get("operator")
        vd = e.get("verdict", "n/a")
        case_id = e.get("case_id", "")
        lines.append(f"- {Path(fp).name}: {op} [{vd}] {case_id}")
    lines.append("")

    lines.append("## Verification summary")
    lines.append(f"- verify pass: {passes} | fail: {fails}")
    lines.append(f"- incidents: {len(incidents)} | replan_count: {replan_count}")
    if delta_mean is not None:
        lines.append(f"- delta_mean: {delta_mean}")
    if summary:
        lines.append(f"- summary.json: {json.dumps(summary, ensure_ascii=False)}")
    lines.append("")

    # Extract a short obligations table (if present)
    lines.append("## Obligations snapshot")
    for e in verifies[:5]:
        ver = e.get("pre", {}).get("verdicts") or {}
        if ver:
            keys = ", ".join([f"{k}:{'✔' if ok else '✖'}" for k, ok in ver.items()])
            lines.append(f"- {e.get('case_id', 'case')} → {keys}")
    lines.append("")

    lines.append("## Attestation")
    lines.append(f"- pcap_count: {att.get('pcap_count')}")
    lines.append(f"- digest: {att.get('digest')}")
    if att.get("verdicts"):
        lines.append("- verdicts:")
        for v in att["verdicts"][:10]:
            lines.append(f"  - {v.get('file')}: {v.get('operator')} [{v.get('verdict')}]")
    lines.append("")

    # Fit & next bar (comment ready to copy in email)
    lines.append("## Comment (fit probe)")
    lines.append(
        "- Direction: hybrid orchestration (stochastic generation inside, deterministic verification outside)."
    )
    lines.append(
        "- Value: reduces supervision cost (PCAP journal, attestation, replayability), structures verification."
    )
    lines.append(
        "- Question: do you see interest in large-scale autoformalization, and what minimum bar would you want for a micro-pilot?"
    )
    lines.append("")

    LOGS_MD.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "pcap": len(pcap_entries),
                "digest": att.get("digest"),
                "logs": str(LOGS_MD),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

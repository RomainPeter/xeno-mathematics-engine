import json, glob, time, hashlib, os
from proofengine.core.schemas import PCAP

def verify_pcap_dir(pcap_dir="out/pcap", audit_out="out/audit"):
    os.makedirs(audit_out, exist_ok=True)
    verdicts = []
    for fp in sorted(glob.glob(os.path.join(pcap_dir, "*.json"))):
        with open(fp, "r", encoding="utf-8") as f:
            entry = PCAP.model_validate_json(f.read())
        verdicts.append({"file": os.path.basename(fp), "operator": entry.operator, "verdict": entry.verdict})
    att = {
        "ts": time.time(),
        "pcap_count": len(verdicts),
        "verdicts": verdicts,
        "digest": hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest()
    }
    with open(os.path.join(audit_out, "attestation.json"), "w", encoding="utf-8") as f:
        json.dump(att, f, indent=2)
    return att

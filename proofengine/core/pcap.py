import hashlib, json, time, os
from .schemas import PCAP

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def merkle_of(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

def write_pcap(entry: PCAP, out_dir="out/pcap") -> str:
    os.makedirs(out_dir, exist_ok=True)
    digest = merkle_of(entry.model_dump())
    path = os.path.join(out_dir, f"{int(time.time()*1000)}_{digest[:8]}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(entry.model_dump_json(indent=2))
    return path

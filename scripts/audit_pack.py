from proofengine.verifier.runner import verify_pcap_dir
import json, os

def main():
    os.makedirs("out/audit", exist_ok=True)
    att = verify_pcap_dir("out/pcap", "out/audit")
    print(json.dumps({"ok": True, "attestation": att}, ensure_ascii=False))

if __name__ == "__main__":
    main()
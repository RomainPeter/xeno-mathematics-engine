from pathlib import Path


def test_verify_detects_tamper(tmp_path: Path):
    from xme.pcap.store import PCAPStore
    from xme.pcap.model import PCAPEntry
    from datetime import datetime, timezone

    store = PCAPStore.new_run(tmp_path)
    store.append(PCAPEntry(action="a1", actor="u", timestamp=datetime.now(timezone.utc)))
    # Tamper: modify a byte in the last line
    p = store.path
    lines = p.read_bytes().splitlines()
    assert len(lines) >= 2
    last = bytearray(lines[-1])
    # flip a char safely (change a digit to letter)
    for i, b in enumerate(last):
        if chr(b).isdigit():
            last[i] = ord('x')
            break
    p.write_bytes(b"\n".join(lines[:-1] + [bytes(last)]) + b"\n")
    ok, reason = store.verify()
    assert not ok and reason in {"hash_mismatch", "chain_broken"}



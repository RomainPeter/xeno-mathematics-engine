from pathlib import Path
from datetime import datetime, timezone
from xme.pcap.store import PCAPStore
from xme.pcap.model import PCAPEntry


def test_chain_and_merkle(tmp_path: Path):
    store = PCAPStore.new_run(tmp_path)
    e1 = store.append(PCAPEntry(action="a1", actor="u", timestamp=datetime.now(timezone.utc)))
    e2 = store.append(PCAPEntry(action="a2", actor="u", timestamp=datetime.now(timezone.utc)))
    ok, reason = store.verify()
    assert ok and reason == "ok"
    root = store.merkle_root()
    assert isinstance(root, str) and len(root) == 64
    assert e2.prev_hash == e1.hash



from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Tuple

import orjson

from xme.pcap.model import PCAPEntry, RunHeader, canonical_dumps, sha256_hex

JSONObj = dict


class PCAPStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    @staticmethod
    def new_run(out_dir: Path) -> "PCAPStore":
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"run-{ts}.jsonl"
        store = PCAPStore(path)
        header = RunHeader(run_id=str(uuid.uuid4()), started_at=datetime.now(timezone.utc))
        store._write_json(header.model_dump())
        return store

    def _write_json(self, obj: JSONObj) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as f:
            f.write(canonical_dumps(obj) + b"\n")

    def _last_hash(self) -> str | None:
        last = None
        for obj in self.read_all():
            if "hash" in obj:
                last = obj["hash"]
        return last

    def append(self, entry: PCAPEntry) -> PCAPEntry:
        prev = self._last_hash()
        entry.prev_hash = prev
        entry.hash = entry.compute_hash()
        self._write_json(entry.model_dump())
        return entry

    def read_all(self) -> Iterator[dict]:
        if not self.path.exists():
            return iter(())

        def _gen() -> Iterator[dict]:
            with self.path.open("rb") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    yield orjson.loads(line)

        return _gen()

    def _leaves(self) -> List[str]:
        return [obj["hash"] for obj in self.read_all() if obj.get("type") == "action"]

    def merkle_root(self) -> str | None:
        leaves = self._leaves()
        if not leaves:
            return None
        level = leaves[:]
        while len(level) > 1:
            nxt: List[str] = []
            for i in range(0, len(level), 2):
                a = level[i]
                b = level[i + 1] if i + 1 < len(level) else level[i]
                nxt.append(sha256_hex((a + b).encode("utf-8")))
            level = nxt
        return level[0]

    def verify(self) -> Tuple[bool, str]:
        # Verify chain and hashes
        last_hash = None
        for obj in self.read_all():
            if obj.get("type") == "run_header":
                last_hash = None
                continue
            if obj.get("type") != "action":
                continue
            payload = dict(obj)
            claimed = payload.pop("hash", None)
            calc = sha256_hex(canonical_dumps(payload))
            if claimed != calc:
                return False, "hash_mismatch"
            if payload.get("prev_hash") != last_hash:
                return False, "chain_broken"
            last_hash = claimed
        return True, "ok"

from __future__ import annotations
from pathlib import Path
from typing import Iterator
import orjson
from xme.pcap.model import PCAPEntry


class PCAPStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, entry: PCAPEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as f:
            f.write(orjson.dumps(entry.model_dump()) + b"\n")

    def read_all(self) -> Iterator[dict]:
        if not self.path.exists():
            return iter(())
        with self.path.open("rb") as f:
            for line in f:
                if line.strip():
                    yield orjson.loads(line)

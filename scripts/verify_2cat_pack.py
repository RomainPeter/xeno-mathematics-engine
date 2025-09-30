import argparse
import hashlib
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify 2cat vendor pack integrity (offline)")
    parser.add_argument("--zip", dest="zip_path", required=True)
    parser.add_argument("--sha256", dest="sha_path", required=True)
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    sha_path = Path(args.sha_path)

    if not zip_path.exists():
        print(f"Missing pack: {zip_path}", file=sys.stderr)
        return 2
    if not sha_path.exists():
        print(f"Missing sha256 file: {sha_path}", file=sys.stderr)
        return 3

    # Read SHA file robustly (handle non-UTF8, extra text); extract first hex digest
    import re

    raw = sha_path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    m = re.search(r"\b([a-fA-F0-9]{64})\b", text)
    if not m:
        print("No SHA256 digest found in sha file", file=sys.stderr)
        return 4
    expected = m.group(1)
    expected_norm = expected.lower()
    actual = sha256_file(zip_path)
    actual_norm = actual.lower()
    if actual_norm != expected_norm:
        print(f"SHA256 mismatch: expected {expected}, got {actual}", file=sys.stderr)
        return 1
    print("2cat pack verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

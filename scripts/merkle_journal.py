#!/usr/bin/env python3
"""
Merkle Journal script for CI artifacts testing
"""
import json
import hashlib
import sys
from pathlib import Path


def calculate_merkle_root(entries):
    """Calculate Merkle root from journal entries"""
    if not entries:
        return "empty"

    # Simple Merkle tree calculation
    hashes = []
    for entry in entries:
        entry_str = json.dumps(entry, sort_keys=True)
        hashes.append(hashlib.sha256(entry_str.encode()).hexdigest())

    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                combined = hashes[i] + hashes[i + 1]
            else:
                combined = hashes[i] + hashes[i]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
        hashes = next_level

    return hashes[0]


def main():
    journal_path = sys.argv[1] if len(sys.argv) > 1 else "orchestrator/journal/J.jsonl"
    merkle_path = sys.argv[2] if len(sys.argv) > 2 else "out/journal/merkle.txt"

    # Create directories
    Path(merkle_path).parent.mkdir(parents=True, exist_ok=True)

    # Read journal entries
    entries = []
    if Path(journal_path).exists():
        with open(journal_path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    # Calculate Merkle root
    merkle_root = calculate_merkle_root(entries)

    # Write Merkle root
    with open(merkle_path, "w") as f:
        f.write(merkle_root)

    print(f"Merkle root: {merkle_root}")
    print(f"Journal entries: {len(entries)}")
    print(f"Merkle root saved to: {merkle_path}")


if __name__ == "__main__":
    main()

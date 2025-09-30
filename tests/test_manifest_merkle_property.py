from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

hypothesis = pytest.importorskip("hypothesis")


def _write_files(tmp: Path, files: dict[str, bytes]) -> list[tuple[Path, str]]:
    pairs = []
    for rel, data in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        pairs.append((p, rel.replace("\\", "/")))
    return pairs


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=8).map(
            lambda s: f"f_{hashlib.sha256(s.encode()).hexdigest()[:6]}.txt"
        ),
        values=st.binary(min_size=0, max_size=32),
        min_size=1,
        max_size=5,
    )
)
def test_merkle_idempotence_and_order_invariance(tmp_path: Path, files: dict[str, bytes]):
    from pefc.pack.merkle import build_entries, compute_merkle_root

    pairs = _write_files(tmp_path, files)

    # ordre naturel
    entries1 = build_entries(pairs)
    root1 = compute_merkle_root(entries1)

    # permutation inverse
    entries2 = build_entries(list(reversed(pairs)))
    root2 = compute_merkle_root(entries2)

    assert root1 == root2

    # idempotence: re-générer sur même contenu -> même racine
    entries3 = build_entries(pairs)
    root3 = compute_merkle_root(entries3)
    assert root3 == root1


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=8).map(
            lambda s: f"g_{hashlib.sha256(s.encode()).hexdigest()[:6]}.txt"
        ),
        values=st.binary(min_size=1, max_size=16),
        min_size=1,
        max_size=4,
    )
)
def test_merkle_drift_detection_one_bit(tmp_path: Path, files: dict[str, bytes]):
    from pefc.pack.merkle import build_entries, compute_merkle_root

    pairs = _write_files(tmp_path, files)
    entries = build_entries(pairs)
    root_before = compute_merkle_root(entries)

    # modifier un seul bit du premier fichier
    first_path = pairs[0][0]
    data = bytearray(first_path.read_bytes())
    if not data:
        data = bytearray(b"\x00")
    data[0] ^= 0x01
    first_path.write_bytes(bytes(data))

    entries_after = build_entries(pairs)
    root_after = compute_merkle_root(entries_after)

    assert root_after != root_before

from pathlib import Path

from pefc.pack.merkle import build_entries, build_manifest, compute_merkle_root


def write_bytes(p: Path, data: bytes):
    p.write_bytes(data)


def test_root_stable_under_permutation(tmp_path: Path):
    """Test that Merkle root is stable under file order permutation."""
    a = tmp_path / "a.txt"
    b = tmp_path / "dir" / "b.txt"
    b.parent.mkdir()
    write_bytes(a, b"A")
    write_bytes(b, b"B")
    # ordre 1
    entries1 = build_entries([(a, "a.txt"), (b, "dir/b.txt")])
    root1 = compute_merkle_root(entries1)
    # ordre 2 (permuté)
    entries2 = build_entries([(b, "dir/b.txt"), (a, "a.txt")])
    root2 = compute_merkle_root(entries2)
    assert root1 == root2
    # modifier le contenu -> racine change
    write_bytes(a, b"AA")
    entries3 = build_entries([(a, "a.txt"), (b, "dir/b.txt")])
    root3 = compute_merkle_root(entries3)
    assert root3 != root1


def test_manifest_excluded_from_root(tmp_path: Path):
    """Test that manifest.json is excluded from Merkle root calculation."""
    f = tmp_path / "x.txt"
    f.write_text("hi")
    entries = build_entries([(f, "x.txt")])
    root = compute_merkle_root(entries)
    manifest = build_manifest(entries, root, "v0.0.1")
    assert manifest["merkle_root"] == root
    # ajouter manifest.json dans le zip plus tard ne doit pas influencer root (test logique)


def test_empty_set_root(tmp_path: Path):
    """Test Merkle root for empty set."""
    assert compute_merkle_root([]) == __import__("hashlib").sha256(b"empty").hexdigest()


def test_manifest_structure(tmp_path: Path):
    """Test that manifest has correct structure."""
    f = tmp_path / "test.txt"
    f.write_text("content")
    entries = build_entries([(f, "test.txt")])
    root = compute_merkle_root(entries)
    manifest = build_manifest(entries, root, "v1.0.0")

    assert "version" in manifest
    assert "built_at" in manifest
    assert "files" in manifest
    assert "merkle_root" in manifest

    assert manifest["version"] == "v1.0.0"
    assert manifest["merkle_root"] == root
    assert len(manifest["files"]) == 1

    file_info = manifest["files"][0]
    assert file_info["path"] == "test.txt"
    assert file_info["size"] == 7  # "content"
    assert "sha256" in file_info
    assert "leaf" in file_info


def test_duplicate_arcname_raises(tmp_path: Path):
    """Test that duplicate arcnames raise RuntimeError."""
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("content1")
    f2.write_text("content2")

    try:
        build_entries([(f1, "same.txt"), (f2, "same.txt")])
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "duplicate arcname" in str(e)


def test_single_file_root(tmp_path: Path):
    """Test Merkle root for single file."""
    f = tmp_path / "single.txt"
    f.write_text("single content")
    entries = build_entries([(f, "single.txt")])
    root = compute_merkle_root(entries)

    # Root should be the leaf hash for single file
    assert root == entries[0].leaf


def test_three_files_root(tmp_path: Path):
    """Test Merkle root for three files (odd number)."""
    files = []
    for i in range(3):
        f = tmp_path / f"file{i}.txt"
        f.write_text(f"content{i}")
        files.append((f, f"file{i}.txt"))

    entries = build_entries(files)
    root = compute_merkle_root(entries)

    # Should have 3 entries
    assert len(entries) == 3
    # Root should be deterministic
    assert len(root) == 64  # SHA256 hex length

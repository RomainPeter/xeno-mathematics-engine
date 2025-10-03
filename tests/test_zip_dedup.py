from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pefc.pack.zipper import add_to_zip, dedup_additional_files


def test_merkle_written_once(tmp_path: Path):
    """Test that merkle.txt is written only once even if attempted multiple times."""
    out = tmp_path / "pack.zip"
    seen = set()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        # merkle via writestr
        add_to_zip(z, "merkle.txt", data=b"abc\n", seen=seen)
        # tenter de le réécrire (doit être ignoré)
        add_to_zip(z, "merkle.txt", data=b"abc\n", seen=seen)
    with ZipFile(out, "r") as z:
        names = z.namelist()
        assert names.count("merkle.txt") == 1


def test_additional_files_dedup_and_collision(tmp_path: Path):
    """Test deduplication of additional files and collision detection."""
    a = tmp_path / "A"
    a.write_text("A")
    b = tmp_path / "B"
    b.write_text("B")
    out = tmp_path / "pack2.zip"
    seen = set()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        # écrire d'abord foo.txt (core)
        add_to_zip(z, "foo.txt", data=b"core", seen=seen)
        # additional propose deux fois foo.txt + bar.txt
        files = [(a, "foo.txt"), (b, "foo.txt"), (b, "bar.txt")]
        filtered = dedup_additional_files(files, seen)
        assert "bar.txt" in {arc for _, arc in filtered}  # foo.txt retiré, bar.txt gardé
        for src, arc in filtered:
            add_to_zip(z, arc, src_path=src, seen=seen)
    with ZipFile(out, "r") as z:
        names = z.namelist()
        assert names.count("foo.txt") == 1
        assert "bar.txt" in names


def test_dedup_additional_files_internal_duplicates(tmp_path: Path):
    """Test that internal duplicates in additional files are removed."""
    a = tmp_path / "file1.txt"
    a.write_text("content1")
    b = tmp_path / "file2.txt"
    b.write_text("content2")

    # Test with internal duplicates
    files = [(a, "duplicate.txt"), (b, "duplicate.txt"), (a, "unique.txt")]
    seen = set()
    filtered = dedup_additional_files(files, seen)

    # Should only have one "duplicate.txt" and one "unique.txt"
    arcnames = [arc for _, arc in filtered]
    assert arcnames.count("duplicate.txt") == 1
    assert "unique.txt" in arcnames
    assert len(filtered) == 2


def test_add_to_zip_validation(tmp_path: Path):
    """Test that add_to_zip validates input parameters correctly."""
    out = tmp_path / "test.zip"
    seen = set()

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        # Test valid usage
        assert add_to_zip(z, "test1.txt", data=b"content", seen=seen) is True
        assert add_to_zip(z, "test2.txt", src_path=test_file, seen=seen) is True

        # Test invalid usage (both src_path and data)
        try:
            add_to_zip(z, "test3.txt", src_path=test_file, data=b"content", seen=seen)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Test invalid usage (neither src_path nor data)
        try:
            add_to_zip(z, "test4.txt", seen=seen)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

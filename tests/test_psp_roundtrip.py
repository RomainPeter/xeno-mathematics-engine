import tempfile
from pathlib import Path

import pytest

from xme.psp.schema import PSP, Block, Cut, Edge, ProofMeta, load_psp


def test_psp_creation():
    """Test basic PSP creation and validation."""
    blocks = [
        Block(id="a", kind="lemma", label="Test Lemma"),
        Block(id="b", kind="proof", label="Test Proof"),
    ]
    edges = [Edge(src="a", dst="b", kind="proves")]
    cuts = [Cut(id="main", blocks=["a", "b"])]

    psp = PSP(blocks=blocks, edges=edges, cuts=cuts)

    assert len(psp.blocks) == 2
    assert len(psp.edges) == 1
    assert psp.dag.acyclic is True
    # DAG metadata is computed during validation, so it should be updated
    assert psp.dag.nodes == 2
    assert psp.dag.edges == 1


def test_psp_acyclic_validation():
    """Test that PSP rejects cyclic graphs."""
    blocks = [
        Block(id="a", kind="lemma"),
        Block(id="b", kind="proof"),
    ]
    edges = [
        Edge(src="a", dst="b", kind="proves"),
        Edge(src="b", dst="a", kind="contradicts"),  # Creates cycle
    ]

    with pytest.raises(ValueError, match="PSP graph must be acyclic"):
        PSP(blocks=blocks, edges=edges)


def test_psp_roundtrip():
    """Test PSP serialization and deserialization."""
    blocks = [
        Block(id="lemma1", kind="lemma", label="Yoneda", data={"key": "value"}),
        Block(id="proof1", kind="proof", label="Proof", data={"method": "direct"}),
    ]
    edges = [Edge(src="lemma1", dst="proof1", kind="proves")]
    cuts = [Cut(id="main", blocks=["lemma1", "proof1"])]
    meta = ProofMeta(theorem="Test Theorem", source="Test Source", tags=["test"])

    psp = PSP(blocks=blocks, edges=edges, cuts=cuts, meta=meta)

    # Test canonical JSON
    json_str = psp.canonical_json()
    assert isinstance(json_str, str)
    assert "lemma1" in json_str
    assert "Yoneda" in json_str

    # Test roundtrip via file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_str)
        temp_path = f.name

    try:
        loaded_psp = load_psp(temp_path)
        assert loaded_psp.blocks[0].id == "lemma1"
        assert loaded_psp.blocks[0].label == "Yoneda"
        assert loaded_psp.meta.theorem == "Test Theorem"
        assert loaded_psp.dag.acyclic is True
    finally:
        Path(temp_path).unlink()


def test_load_example_files():
    """Test loading the example PSP files."""
    yoneda_path = Path("examples/psp/mock_yoneda.json")
    ch22_path = Path("examples/psp/mock_ch22.json")

    if yoneda_path.exists():
        yoneda_psp = load_psp(yoneda_path)
        assert yoneda_psp.meta.theorem == "Yoneda Lemma"
        assert len(yoneda_psp.blocks) == 3
        assert yoneda_psp.dag.acyclic is True

    if ch22_path.exists():
        ch22_psp = load_psp(ch22_path)
        assert "Fundamental group" in ch22_psp.meta.theorem
        assert len(ch22_psp.blocks) == 5
        assert ch22_psp.dag.acyclic is True

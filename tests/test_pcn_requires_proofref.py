"""
Tests pour le PCN et les exigences de preuve.
"""

from pathlib import Path

from xme.referee.alien_reserve import AlienReserve
from xme.referee.referee import Referee


def test_baptize_requires_proof_ref(tmp_path: Path):
    """Test que le baptême nécessite une preuve."""
    r = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")

    # S'assurer que le lineage n'est pas sous embargo
    AlienReserve(tmp_path / "reserve.json").release("XLINE", "init")

    # Essayer de baptiser sans preuve
    verdict = r.gate_baptism("XLINE", "C42", "Xi_1", proof_ref=None, pcap=None)
    assert not verdict["ok"]
    assert verdict["reason"] == "missing_proof_ref"


def test_baptize_requires_valid_symbol(tmp_path: Path):
    """Test que le symbole doit respecter le charset."""
    r = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")

    # S'assurer que le lineage n'est pas sous embargo
    AlienReserve(tmp_path / "reserve.json").release("XLINE", "init")

    # Essayer de baptiser avec un symbole invalide
    verdict = r.gate_baptism("XLINE", "C42", "Xi-1", proof_ref="proof123", pcap=None)
    assert not verdict["ok"]
    assert verdict["reason"] == "invalid_symbol_charset"


def test_baptize_blocks_embargoed_lineage(tmp_path: Path):
    """Test que le baptême est bloqué pour un lineage sous embargo."""
    r = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")

    # Mettre le lineage sous embargo
    r.reserve.register("XLINE", {"area": "demo"})

    # Essayer de baptiser
    verdict = r.gate_baptism("XLINE", "C42", "Xi_1", proof_ref="proof123", pcap=None)
    assert not verdict["ok"]
    assert verdict["reason"] == "embargoed"


def test_baptize_success(tmp_path: Path):
    """Test un baptême réussi."""
    r = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")

    # S'assurer que le lineage n'est pas sous embargo
    AlienReserve(tmp_path / "reserve.json").release("XLINE", "init")

    # Baptiser avec succès
    verdict = r.gate_baptism("XLINE", "C42", "Xi_1", proof_ref="proof123", pcap=None)
    assert verdict["ok"]
    assert "entry" in verdict
    assert verdict["entry"]["concept_id"] == "C42"
    assert verdict["entry"]["symbol"] == "Xi_1"
    assert verdict["entry"]["proof_ref"] == "proof123"


def test_baptize_multiple_symbols(tmp_path: Path):
    """Test le baptême de plusieurs symboles."""
    r = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")

    # S'assurer que le lineage n'est pas sous embargo
    AlienReserve(tmp_path / "reserve.json").release("XLINE", "init")

    # Baptiser plusieurs symboles
    verdict1 = r.gate_baptism("XLINE", "C1", "Xi_1", proof_ref="proof1", pcap=None)
    verdict2 = r.gate_baptism("XLINE", "C2", "Xi_2", proof_ref="proof2", pcap=None)

    assert verdict1["ok"]
    assert verdict2["ok"]

    # Vérifier que les deux symboles sont dans le store
    symbols = r.symbols.list()
    assert len(symbols) == 2
    assert symbols[0].symbol == "Xi_1"
    assert symbols[1].symbol == "Xi_2"


def test_baptize_persistence(tmp_path: Path):
    """Test la persistance des symboles baptisés."""
    # Premier Referee
    r1 = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")
    AlienReserve(tmp_path / "reserve.json").release("XLINE", "init")

    verdict = r1.gate_baptism("XLINE", "C42", "Xi_1", proof_ref="proof123", pcap=None)
    assert verdict["ok"]

    # Deuxième Referee (même fichiers)
    r2 = Referee(tmp_path / "cfg.json", tmp_path / "reserve.json", tmp_path / "symbols.json")
    symbols = r2.symbols.list()
    assert len(symbols) == 1
    assert symbols[0].symbol == "Xi_1"
    assert symbols[0].concept_id == "C42"

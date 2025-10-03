"""
Tests pour l'embargo des X-lineages.
"""

from pathlib import Path

from xme.referee.alien_reserve import AlienReserve


def test_embargo_blocks_then_release(tmp_path: Path):
    """Test que l'embargo bloque puis libère correctement."""
    res = AlienReserve(tmp_path / "reserve.json")

    # Enregistrer un lineage
    res.register("X123", {"area": "demo"})
    assert res.is_embargoed("X123")

    # Libérer le lineage
    assert res.release("X123", "criteria met")
    assert not res.is_embargoed("X123")


def test_embargo_multiple_lineages(tmp_path: Path):
    """Test la gestion de plusieurs lineages."""
    res = AlienReserve(tmp_path / "reserve.json")

    # Enregistrer plusieurs lineages
    res.register("X1", {"area": "demo1"})
    res.register("X2", {"area": "demo2"})
    res.register("X3", {"area": "demo3"})

    # Vérifier que tous sont sous embargo
    assert res.is_embargoed("X1")
    assert res.is_embargoed("X2")
    assert res.is_embargoed("X3")

    # Libérer seulement X2
    assert res.release("X2", "ok")
    assert not res.is_embargoed("X2")
    assert res.is_embargoed("X1")
    assert res.is_embargoed("X3")


def test_embargo_nonexistent_lineage(tmp_path: Path):
    """Test la gestion d'un lineage inexistant."""
    res = AlienReserve(tmp_path / "reserve.json")

    # Essayer de libérer un lineage inexistant
    assert not res.release("NONEXISTENT", "ok")
    assert not res.is_embargoed("NONEXISTENT")


def test_embargo_list(tmp_path: Path):
    """Test la liste des lineages."""
    res = AlienReserve(tmp_path / "reserve.json")

    # Enregistrer quelques lineages
    res.register("X1", {"area": "demo1"})
    res.register("X2", {"area": "demo2"})
    res.release("X2", "ok")

    # Vérifier la liste
    lineages = res.list()
    assert "X1" in lineages
    assert "X2" in lineages
    assert lineages["X1"]["embargoed"] is True
    assert lineages["X2"]["embargoed"] is False
    assert lineages["X2"]["release_reason"] == "ok"


def test_embargo_persistence(tmp_path: Path):
    """Test la persistance des données."""
    # Créer et enregistrer
    res1 = AlienReserve(tmp_path / "reserve.json")
    res1.register("X123", {"area": "demo"})
    assert res1.is_embargoed("X123")

    # Recréer et vérifier que les données sont persistées
    res2 = AlienReserve(tmp_path / "reserve.json")
    assert res2.is_embargoed("X123")

    # Libérer et vérifier la persistance
    res2.release("X123", "ok")
    res3 = AlienReserve(tmp_path / "reserve.json")
    assert not res3.is_embargoed("X123")

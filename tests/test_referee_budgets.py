"""
Tests pour les budgets H/X.
"""

from xme.referee.budgets import BudgetsHX, BudgetTracker


def test_budgets_consume_and_block():
    """Test que la consommation de budget fonctionne et bloque quand nécessaire."""
    tr = BudgetTracker(BudgetsHX(h_quota=2, x_quota=1))

    # Consommer H
    assert tr.consume("H", 1)
    assert tr.consume("H", 1)
    assert not tr.consume("H", 1)  # Doit échouer

    # Consommer X
    assert tr.consume("X", 1)
    assert not tr.consume("X", 1)  # Doit échouer


def test_budgets_remaining():
    """Test le calcul du budget restant."""
    tr = BudgetTracker(BudgetsHX(h_quota=5, x_quota=3))

    assert tr.remaining("H") == 5
    assert tr.remaining("X") == 3

    tr.consume("H", 2)
    tr.consume("X", 1)

    assert tr.remaining("H") == 3
    assert tr.remaining("X") == 2


def test_budgets_report():
    """Test le rapport des budgets."""
    tr = BudgetTracker(BudgetsHX(h_quota=10, x_quota=20))

    tr.consume("H", 3)
    tr.consume("X", 7)

    report = tr.report()
    assert report["H_used"] == 3
    assert report["H_remaining"] == 7
    assert report["X_used"] == 7
    assert report["X_remaining"] == 13


def test_budgets_negative_consume():
    """Test que la consommation négative est gérée."""
    tr = BudgetTracker(BudgetsHX(h_quota=5, x_quota=5))

    # Consommer plus que disponible
    assert not tr.consume("H", 10)
    assert not tr.consume("X", 10)

    # Le budget ne doit pas être négatif
    assert tr.remaining("H") == 5
    assert tr.remaining("X") == 5

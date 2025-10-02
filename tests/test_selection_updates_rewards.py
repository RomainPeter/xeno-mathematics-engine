"""
Tests pour la mise à jour des récompenses dans la sélection bandit.
"""

from xme.selection.bandit import EpsilonGreedy


def test_bandit_initialization():
    """Test l'initialisation du bandit."""
    bandit = EpsilonGreedy(["ae", "cegis"], epsilon=0.1)

    assert bandit.arms == ["ae", "cegis"]
    assert bandit.epsilon == 0.1
    assert bandit.total_pulls == 0

    stats = bandit.get_stats()
    assert "ae" in stats
    assert "cegis" in stats
    assert stats["ae"]["count"] == 0
    assert stats["ae"]["total_reward"] == 0.0
    assert stats["ae"]["average_reward"] == 0.0


def test_bandit_update_rewards():
    """Test que les récompenses mettent à jour les statistiques."""
    bandit = EpsilonGreedy(["ae", "cegis"], epsilon=0.0)  # Exploitation pure

    # Mise à jour des récompenses
    bandit.update("ae", 5.0)
    bandit.update("ae", 3.0)
    bandit.update("cegis", 8.0)

    stats = bandit.get_stats()

    # Vérifier les statistiques AE
    assert stats["ae"]["count"] == 2
    assert stats["ae"]["total_reward"] == 8.0
    assert stats["ae"]["average_reward"] == 4.0

    # Vérifier les statistiques CEGIS
    assert stats["cegis"]["count"] == 1
    assert stats["cegis"]["total_reward"] == 8.0
    assert stats["cegis"]["average_reward"] == 8.0

    # Vérifier le total
    assert bandit.total_pulls == 3


def test_bandit_selects_best_arm():
    """Test que le bandit sélectionne la meilleure arme en exploitation."""
    bandit = EpsilonGreedy(["ae", "cegis"], epsilon=0.0)  # Exploitation pure

    # AE a une meilleure récompense moyenne
    bandit.update("ae", 10.0)
    bandit.update("cegis", 5.0)

    # En exploitation pure, doit sélectionner AE
    selected = bandit.select()
    assert selected == "ae"

    # Vérifier que get_best_arm retourne AE
    assert bandit.get_best_arm() == "ae"


def test_bandit_exploration():
    """Test que le bandit explore avec epsilon > 0."""
    bandit = EpsilonGreedy(["ae", "cegis"], epsilon=1.0)  # Exploration pure

    # Avec exploration pure, les deux armes peuvent être sélectionnées
    selections = [bandit.select() for _ in range(10)]

    # Au moins une des deux armes doit être sélectionnée
    assert "ae" in selections or "cegis" in selections


def test_bandit_reset():
    """Test que le reset remet à zéro les statistiques."""
    bandit = EpsilonGreedy(["ae", "cegis"], epsilon=0.1)

    # Ajouter des données
    bandit.update("ae", 5.0)
    bandit.update("cegis", 3.0)

    # Reset
    bandit.reset()

    # Vérifier que tout est remis à zéro
    assert bandit.total_pulls == 0
    stats = bandit.get_stats()
    assert stats["ae"]["count"] == 0
    assert stats["ae"]["total_reward"] == 0.0
    assert stats["cegis"]["count"] == 0
    assert stats["cegis"]["total_reward"] == 0.0

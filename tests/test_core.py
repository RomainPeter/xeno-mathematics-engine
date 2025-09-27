"""
Tests unitaires pour les modules centraux.
"""

import pytest
from proofengine.core.schemas import VJustification, Proof, PCAP, XState
from proofengine.core.hashing import hash_state, hash_pcap, verify_state_integrity
from proofengine.core.state import create_initial_state, StateManager
from proofengine.core.delta import DeltaCalculator


class TestVCost:
    """Tests pour la classe VJustification."""

    def test_vcost_creation(self):
        """Test de création d'un VJustification."""
        cost = VJustification(
            time_ms=100, retries=2, backtracks=1, audit_cost=1.5, risk=0.3, tech_debt=0
        )

        assert cost.time_ms == 100
        assert cost.retries == 2
        assert cost.backtracks == 1
        assert cost.audit_cost == 1.5
        assert cost.risk == 0.3
        assert cost.tech_debt == 0

    def test_vcost_to_dict(self):
        """Test de sérialisation VJustification."""
        cost = VJustification(
            time_ms=50, retries=1, backtracks=0, audit_cost=0.8, risk=0.2, tech_debt=1
        )
        cost_dict = cost.to_dict()

        assert isinstance(cost_dict, dict)
        assert cost_dict["time_ms"] == 50
        assert cost_dict["retries"] == 1


class TestProof:
    """Tests pour la classe Proof."""

    def test_proof_creation(self):
        """Test de création d'une Proof."""
        proof = Proof(
            kind="unit",
            name="test_proof",
            passed=True,
            logs="Test successful",
            artifacts=["test_file.py"],
        )

        assert proof.kind == "unit"
        assert proof.name == "test_proof"
        assert proof.passed == True
        assert proof.logs == "Test successful"
        assert proof.artifacts == ["test_file.py"]

    def test_proof_serialization(self):
        """Test de sérialisation Proof."""
        proof = Proof(kind="policy", name="security_check", passed=False, logs="Failed")
        proof_dict = proof.to_dict()

        assert isinstance(proof_dict, dict)
        assert proof_dict["kind"] == "policy"
        assert proof_dict["passed"] == False


class TestXState:
    """Tests pour la classe XState."""

    def test_xstate_creation(self):
        """Test de création d'un XState."""
        state = XState(
            H={"hypothesis1", "hypothesis2"},
            E={"evidence1"},
            K=[{"policy": "test"}],
            A=["artifact1.py"],
            J=["pcap1", "pcap2"],
            Sigma={"seed": 42},
            state_hash="test_hash",
        )

        assert len(state.H) == 2
        assert "hypothesis1" in state.H
        assert len(state.E) == 1
        assert len(state.K) == 1
        assert state.Sigma["seed"] == 42

    def test_xstate_serialization(self):
        """Test de sérialisation XState."""
        state = create_initial_state(
            hypotheses={"test_hyp"},
            evidences={"test_ev"},
            obligations=[{"policy": "test"}],
            artifacts=["test.py"],
            sigma={"seed": 123},
        )

        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert "test_hyp" in state_dict["H"]


class TestHashing:
    """Tests pour le système de hachage."""

    def test_hash_state(self):
        """Test de hachage d'état."""
        state = create_initial_state(
            hypotheses={"hyp1", "hyp2"}, evidences={"ev1"}, sigma={"seed": 42}
        )

        hash1 = hash_state(state)
        hash2 = hash_state(state)

        # Le hash doit être déterministe
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256

    def test_hash_pcap(self):
        """Test de hachage PCAP."""
        pcap = PCAP(
            operator="test",
            action="test_action",
            pre_hash="pre_hash",
            post_hash="post_hash",
            obligations=["test_obligation"],
            justification=VJustification(
                time_ms=100,
                retries=0,
                backtracks=0,
                audit_cost=1.0,
                risk=0.1,
                tech_debt=0,
            ),
            proofs=[],
            verdict="pass",
            toolchain={"version": "1.0"},
            pcap_hash="",
        )

        hash_value = hash_pcap(pcap)
        assert len(hash_value) == 64
        assert hash_value != pcap.pcap_hash  # Hash calculé vs stocké

    def test_verify_state_integrity(self):
        """Test de vérification d'intégrité d'état."""
        state = create_initial_state()
        state.state_hash = hash_state(state)

        assert verify_state_integrity(state) == True

        # Modifier l'état sans recalculer le hash
        state.H.add("new_hypothesis")
        assert verify_state_integrity(state) == False


class TestStateManager:
    """Tests pour le gestionnaire d'état."""

    def test_state_manager_creation(self):
        """Test de création d'un StateManager."""
        initial_state = create_initial_state()
        manager = StateManager(initial_state)

        assert manager.current_state == initial_state
        assert len(manager.snapshots) == 0
        assert len(manager.journal) == 0

    def test_snapshot_and_rollback(self):
        """Test de snapshot et rollback."""
        initial_state = create_initial_state()
        manager = StateManager(initial_state)

        # Créer un snapshot
        snapshot_id = manager.snapshot()
        assert len(manager.snapshots) == 1

        # Modifier l'état
        manager.current_state.H.add("new_hypothesis")

        # Rollback
        success = manager.rollback(snapshot_id)
        assert success == True
        assert "new_hypothesis" not in manager.current_state.H

    def test_add_rule_from_incident(self):
        """Test d'ajout de règle depuis un incident."""
        initial_state = create_initial_state()
        manager = StateManager(initial_state)

        # Créer un PCAP d'incident
        incident_pcap = PCAP(
            operator="test",
            action="failed_action",
            pre_hash="pre",
            post_hash="post",
            obligations=["test_obligation"],
            justification=VJustification(
                time_ms=100,
                retries=1,
                backtracks=0,
                audit_cost=2.0,
                risk=0.8,
                tech_debt=1,
            ),
            proofs=[],
            verdict="fail",
            toolchain={},
            pcap_hash="incident_hash",
        )

        # Ajouter la règle
        manager.add_rule_from_incident(incident_pcap, "forbidden")

        # Vérifier que la règle a été ajoutée
        assert len(manager.current_state.K) == 1
        rule = manager.current_state.K[0]
        assert rule["type"] == "forbidden"
        assert rule["trigger"] == "failed_action"


class TestDeltaCalculator:
    """Tests pour le calculateur de delta."""

    def test_delta_calculator_creation(self):
        """Test de création d'un DeltaCalculator."""
        calculator = DeltaCalculator()
        assert calculator.weights is not None
        assert "H" in calculator.weights
        assert "E" in calculator.weights

    def test_calculate_delta(self):
        """Test de calcul de delta."""
        calculator = DeltaCalculator()

        # Créer deux états
        old_state = create_initial_state(
            hypotheses={"hyp1"}, evidences={"ev1"}, artifacts=["art1.py"]
        )

        new_state = create_initial_state(
            hypotheses={"hyp1", "hyp2"},
            evidences={"ev1", "ev2"},
            artifacts=["art1.py", "art2.py"],
        )

        delta_result = calculator.calculate_delta(old_state, new_state)

        assert "delta_total" in delta_result
        assert "components" in delta_result
        assert delta_result["delta_total"] > 0  # Il devrait y avoir une différence

    def test_jaccard_similarity(self):
        """Test de similarité de Jaccard."""
        from proofengine.core.delta import jaccard_similarity

        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}

        similarity = jaccard_similarity(set1, set2)
        assert 0 <= similarity <= 1
        assert similarity == 0.5  # 2 éléments communs sur 4 total

    def test_edit_distance(self):
        """Test de distance d'édition."""
        from proofengine.core.delta import edit_distance

        seq1 = ["a", "b", "c"]
        seq2 = ["a", "b", "d"]

        distance = edit_distance(seq1, seq2)
        assert distance == 1  # Un changement


if __name__ == "__main__":
    pytest.main([__file__])

"""
Tests for AE Next-Closure loop.
"""

import os
# Import our modules
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from methods.ae.next_closure import AEExplorer
from methods.ae.oracle import Oracle
from orchestrator.state import XState


class TestAEExplorer:
    """Test AE Explorer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.state = XState()
        self.domain_spec = {
            "id": "test_domain",
            "oracle_endpoints": {"opa_cmd": "opa", "rego_pkg": "policy"},
            "timeouts": {"verify_ms": 5000},
        }
        self.verifier = Mock()
        self.bandit = Mock()
        self.diversity = Mock()

        # Configure mocks
        self.diversity.select_diverse_items.return_value = [
            {"id": "imp_1", "premises": ["A"], "conclusions": ["B"]},
            {"id": "imp_2", "premises": ["C"], "conclusions": ["D"]},
        ]

        self.explorer = AEExplorer(
            self.state, self.verifier, self.domain_spec, self.bandit, self.diversity
        )

    def test_propose_implications(self):
        """Test implication proposal."""
        implications = self.explorer.propose(k=2)

        assert len(implications) == 2
        assert all("canonical_hash" in imp for imp in implications)
        assert all("canonical_representative" in imp for imp in implications)

        # Verify diversity was called
        self.diversity.select_diverse_items.assert_called_once()

    def test_verify_implication(self):
        """Test implication verification."""
        implication = {"id": "test_imp", "premises": ["A"], "conclusions": ["B"]}

        # Mock verifier response
        self.verifier.verify_implication.return_value = {
            "valid": True,
            "attestation": {"type": "test"},
        }

        result = self.explorer.verify(implication)

        assert result["valid"] is True
        self.verifier.verify_implication.assert_called_once_with(implication)

    def test_incorporate_valid_implication(self):
        """Test incorporating valid implication."""
        implication = {"id": "valid_imp", "premises": ["A"], "conclusions": ["B"]}

        initial_journal_len = len(self.explorer.journal)

        self.explorer.incorporate_valid(implication)

        # Check state was updated
        assert len(self.state.H) == 1

        # Check journal was updated
        assert len(self.explorer.journal) == initial_journal_len + 1

        # Check DCA structure
        dca = self.explorer.journal[-1]
        assert dca["verdict"] == "accept"
        assert dca["context"] == implication
        assert "attestation" in dca

    def test_incorporate_counterexample(self):
        """Test incorporating counterexample."""
        implication = {"id": "invalid_imp", "premises": ["A"], "conclusions": ["B"]}
        counterexample = {"id": "cex_1", "data": "counterexample data"}

        initial_journal_len = len(self.explorer.journal)
        initial_K_len = len(self.state.K)

        self.explorer.incorporate_cex(implication, counterexample)

        # Check state was updated
        assert len(self.state.E) == 1
        assert len(self.state.K) == initial_K_len + 1

        # Check journal was updated
        assert len(self.explorer.journal) == initial_journal_len + 1

        # Check DCA structure
        dca = self.explorer.journal[-1]
        assert dca["verdict"] == "reject"
        assert dca["counterexample_ref"] == counterexample["id"]

    def test_run_ae_loop(self):
        """Test running the complete AE loop."""
        # Mock verifier responses
        self.verifier.verify_implication.side_effect = [
            {"valid": True, "attestation": {"type": "test"}},
            {"valid": False, "counterexample": {"id": "cex_1", "data": "test"}},
            {"valid": True, "attestation": {"type": "test"}},
        ]

        budgets = {"max_iterations": 3}
        thresholds = {"coverage_gain_min": 0.05, "novelty_min": 0.2}

        results = self.explorer.run(budgets, thresholds)

        # Check results structure
        assert "implications_accepted" in results
        assert "counterexamples_found" in results
        assert "rules_generated" in results
        assert "journal_entries" in results

        # Check that some processing occurred
        assert results["journal_entries"] > 0


class TestOracle:
    """Test Oracle functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.domain_spec = {
            "oracle_endpoints": {"opa_cmd": "opa", "rego_pkg": "policy"},
            "timeouts": {"verify_ms": 5000},
        }
        self.oracle = Oracle(self.domain_spec)

    def test_create_opa_input(self):
        """Test OPA input creation."""
        implication = {
            "premises": ["data_class=sensitive", "has_legal_basis"],
            "conclusions": ["access_granted"],
        }

        input_data = self.oracle._create_opa_input(implication)

        assert "data_class" in input_data
        assert input_data["data_class"] == "sensitive"
        assert input_data["has_legal_basis"] is True

    @patch("subprocess.run")
    def test_run_opa_evaluation_success(self, mock_run):
        """Test successful OPA evaluation."""
        # Mock successful OPA run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"result": []}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        input_data = {"data_class": "sensitive", "has_legal_basis": True}

        result = self.oracle._run_opa_evaluation(input_data)

        assert result["valid"] is True
        assert result["deny_results"] == []

    @patch("subprocess.run")
    def test_run_opa_evaluation_failure(self, mock_run):
        """Test failed OPA evaluation."""
        # Mock failed OPA run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"result": ["Missing legal basis"]}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        input_data = {"data_class": "sensitive", "has_legal_basis": False}

        result = self.oracle._run_opa_evaluation(input_data)

        assert result["valid"] is False
        assert "Missing legal basis" in result["deny_results"]

    def test_generate_counterexample(self):
        """Test counterexample generation."""
        implication = {"id": "test_imp", "premises": ["A"], "conclusions": ["B"]}
        opa_result = {"valid": False, "deny_results": ["Policy violation"]}
        static_result = {"valid": True, "issues": []}

        counterexample = self.oracle._generate_counterexample(
            implication, opa_result, static_result
        )

        assert counterexample["implication_id"] == "test_imp"
        assert counterexample["type"] == "verification_failure"
        assert "Policy violation" in counterexample["opa_deny_results"]
        assert "timestamp" in counterexample


class TestAEIntegration:
    """Integration tests for AE components."""

    def test_ae_acceptance_criteria(self):
        """Test AE acceptance criteria: 3 accepted, 1 rejected → counterexample → K↑."""
        # Set up test environment
        state = XState()
        domain_spec = {
            "oracle_endpoints": {"opa_cmd": "opa", "rego_pkg": "policy"},
            "timeouts": {"verify_ms": 5000},
        }

        # Mock verifier to return specific results
        verifier = Mock()
        verifier.verify_implication.side_effect = [
            {"valid": True, "attestation": {"type": "test"}},  # Accept 1
            {"valid": True, "attestation": {"type": "test"}},  # Accept 2
            {"valid": True, "attestation": {"type": "test"}},  # Accept 3
            {
                "valid": False,
                "counterexample": {  # Reject 1
                    "id": "cex_1",
                    "data": "test counterexample",
                    "type": "verification_failure",
                },
            },
        ]

        # Mock diversity selector
        diversity = Mock()
        diversity.select_diverse_items.return_value = [
            {"id": f"imp_{i}", "premises": [f"attr_{i}"], "conclusions": [f"concl_{i}"]}
            for i in range(4)
        ]

        bandit = Mock()

        explorer = AEExplorer(state, verifier, domain_spec, bandit, diversity)

        # Run AE loop
        budgets = {"max_iterations": 1}
        thresholds = {"coverage_gain_min": 0.05, "novelty_min": 0.2}

        results = explorer.run(budgets, thresholds)

        # Verify acceptance criteria
        assert results["implications_accepted"] >= 3
        assert results["counterexamples_found"] >= 1
        assert results["rules_generated"] >= 1  # K↑ from counterexample

        # Verify journal is Merklized (has entries)
        assert results["journal_entries"] > 0

        print("✅ AE Acceptance Criteria Met:")
        print(f"   - Implications accepted: {results['implications_accepted']}")
        print(f"   - Counterexamples found: {results['counterexamples_found']}")
        print(f"   - Rules generated: {results['rules_generated']}")
        print(f"   - Journal entries: {results['journal_entries']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

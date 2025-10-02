"""
Tests for incident handlers (FailReason v1).
"""

import os

# Import our modules
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.handlers.failreason import FailReason, FailReasonCategory, IncidentHandler


class TestIncidentHandler:
    """Test IncidentHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = IncidentHandler()
        self.mock_state = {
            "H": {"imp1": {"id": "imp1", "premises": ["A"], "conclusions": ["B"]}},
            "E": {"cex1": {"id": "cex1", "data": "counterexample"}},
            "K": {"rule1": {"id": "rule1", "content": "existing rule"}},
        }

    def test_extract_fail_reason_low_novelty(self):
        """Test extracting low novelty failure reason."""
        incident = {
            "id": "inc1",
            "type": "low_novelty_implication",
            "details": {"novelty_score": 0.1},
        }

        fail_reason = self.handler._extract_fail_reason(incident)

        assert fail_reason.code == "LowNovelty"
        assert fail_reason.category == FailReasonCategory.NOVELTY
        assert "low novelty" in fail_reason.message.lower()

    def test_extract_fail_reason_low_coverage(self):
        """Test extracting low coverage failure reason."""
        incident = {
            "id": "inc2",
            "type": "low_coverage_implication",
            "details": {"coverage_gain": 0.02},
        }

        fail_reason = self.handler._extract_fail_reason(incident)

        assert fail_reason.code == "LowCoverage"
        assert fail_reason.category == FailReasonCategory.COVERAGE
        assert "coverage" in fail_reason.message.lower()

    def test_extract_fail_reason_constraint_breach(self):
        """Test extracting constraint breach failure reason."""
        incident = {
            "id": "inc3",
            "type": "constraint_violation",
            "details": {"constraint": "legal_basis_required"},
        }

        fail_reason = self.handler._extract_fail_reason(incident)

        assert fail_reason.code == "ConstraintBreach"
        assert fail_reason.category == FailReasonCategory.POLICY
        assert "constraint" in fail_reason.message.lower()

    def test_handle_low_novelty_incident(self):
        """Test handling low novelty incident."""
        incident = {
            "id": "inc1",
            "type": "low_novelty_implication",
            "implication": {
                "id": "imp1",
                "premises": ["A"],
                "conclusions": ["B"],
                "variant": {"premises": ["A"], "conclusions": ["B"]},
            },
            "details": {"novelty_score": 0.1},
        }

        result = self.handler.handle_incident(incident, self.mock_state)

        assert "updated_state" in result
        assert "generated_rule" in result
        assert "handler_result" in result
        assert "replanning_required" in result

        # Check that rule was added to K
        updated_state = result["updated_state"]
        assert len(updated_state["K"]) > len(self.mock_state["K"])

        # Check that forbidden equivalence was added
        assert "forbidden_equivalences" in updated_state
        assert len(updated_state["forbidden_equivalences"]) == 1

    def test_handle_low_coverage_incident(self):
        """Test handling low coverage incident."""
        incident = {
            "id": "inc2",
            "type": "low_coverage_implication",
            "implication": {"id": "imp2", "premises": ["C"], "conclusions": ["D"]},
            "details": {"coverage_gap": 0.1},
        }

        result = self.handler.handle_incident(incident, self.mock_state)

        # Check that coverage target was added
        updated_state = result["updated_state"]
        assert "coverage_targets" in updated_state
        assert len(updated_state["coverage_targets"]) == 1

        # Check that policy update was applied
        handler_result = result["handler_result"]
        assert handler_result["action"] == "add_target_in_K"
        assert "target" in handler_result
        assert "policy_update" in handler_result

    def test_handle_constraint_breach_incident(self):
        """Test handling constraint breach incident."""
        incident = {
            "id": "inc3",
            "type": "constraint_violation",
            "constraint": {
                "id": "legal_basis",
                "condition": "input.has_legal_basis",
                "message": "Legal basis required",
            },
            "violation": {
                "input": {"data_class": "sensitive", "has_legal_basis": False},
                "path": ["data_access", "sensitive_data"],
            },
        }

        result = self.handler.handle_incident(incident, self.mock_state)

        # Check that OPA rule was generated
        handler_result = result["handler_result"]
        assert handler_result["action"] == "add_opa_rule_and_test"
        assert "opa_rule" in handler_result
        assert "test" in handler_result
        assert "blocked_path" in handler_result

        # Check rule content
        opa_rule = handler_result["opa_rule"]
        assert "deny[msg]" in opa_rule["content"]
        assert "Legal basis required" in opa_rule["content"]

    def test_handle_oracle_timeout_incident(self):
        """Test handling oracle timeout incident."""
        incident = {
            "id": "inc4",
            "type": "oracle_timeout",
            "timeout_ms": 8000,
            "problematic_seeds": ["seed1", "seed2"],
        }

        result = self.handler.handle_incident(incident, self.mock_state)

        # Check that timeout was increased
        handler_result = result["handler_result"]
        assert handler_result["action"] == "increase_budget_or_quarantine"
        assert "timeout_update" in handler_result
        assert "quarantine" in handler_result

        timeout_update = handler_result["timeout_update"]
        assert timeout_update["new_timeout_ms"] > timeout_update["old_timeout_ms"]

    def test_handle_flaky_incident(self):
        """Test handling flaky incident."""
        incident = {
            "id": "inc5",
            "type": "flaky_behavior",
            "flaky_seeds": ["seed3", "seed4"],
            "retry_count": 2,
        }

        result = self.handler.handle_incident(incident, self.mock_state)

        # Check that seeds were quarantined
        handler_result = result["handler_result"]
        assert handler_result["action"] == "quarantine_seeds"
        assert "quarantine" in handler_result
        assert "robustness_update" in handler_result

        quarantine = handler_result["quarantine"]
        assert len(quarantine["seeds"]) == 2
        assert "seed3" in quarantine["seeds"]
        assert "seed4" in quarantine["seeds"]

    def test_generate_rule_from_incident(self):
        """Test generating rule from incident."""
        incident = {"id": "inc1", "type": "test_incident", "details": {"test": "value"}}

        fail_reason = FailReason(
            code="TestReason",
            message="Test failure",
            category=FailReasonCategory.RUNTIME,
            details={"test": "value"},
            handler_action="test_handler",
        )

        handler_result = {"action": "test_action", "description": "Test handler result"}

        rule = self.handler._generate_rule_from_incident(incident, fail_reason, handler_result)

        assert rule["type"] == "incident_generated_rule"
        assert rule["incident_id"] == "inc1"
        assert rule["fail_reason"] == "TestReason"
        assert rule["handler_action"] == "test_action"
        assert "incident" in rule["details"]
        assert "fail_reason" in rule["details"]
        assert "handler_result" in rule["details"]

    def test_update_state_with_rule(self):
        """Test updating state with generated rule."""
        rule = {
            "id": "rule_test",
            "handler_action": "egraph_add_equiv_forbidden",
            "details": {
                "handler_result": {
                    "forbidden_equivalence": {
                        "type": "forbidden_equivalence",
                        "implication_id": "imp1",
                    }
                }
            },
        }

        updated_state = self.handler._update_state_with_rule(self.mock_state, rule)

        # Check that rule was added to K
        assert rule["id"] in updated_state["K"]

        # Check that forbidden equivalence was added
        assert "forbidden_equivalences" in updated_state
        assert len(updated_state["forbidden_equivalences"]) == 1

    def test_should_replan(self):
        """Test replanning decision logic."""
        # Test cases that should trigger replanning
        replan_actions = [
            "add_target_in_K",
            "add_opa_rule_and_test",
            "increase_budget_or_quarantine",
        ]

        for action in replan_actions:
            fail_reason = FailReason("Test", "Test", FailReasonCategory.RUNTIME, {}, action)
            handler_result = {"action": action}

            should_replan = self.handler._should_replan(fail_reason, handler_result)
            assert should_replan, f"Action {action} should trigger replanning"

        # Test case that should not trigger replanning
        fail_reason = FailReason(
            "Test", "Test", FailReasonCategory.RUNTIME, {}, "egraph_add_equiv_forbidden"
        )
        handler_result = {"action": "egraph_add_equiv_forbidden"}

        should_replan = self.handler._should_replan(fail_reason, handler_result)
        assert not should_replan, "egraph_add_equiv_forbidden should not trigger replanning"

    def test_get_incident_stats(self):
        """Test getting incident statistics."""
        # Initially no incidents
        stats = self.handler.get_incident_stats()
        assert stats["total_incidents"] == 0
        assert stats["total_rules_generated"] == 0

        # Add some incidents
        incident1 = {
            "id": "inc1",
            "type": "low_novelty_implication",
            "implication": {"id": "imp1"},
            "details": {"novelty_score": 0.1},
        }

        incident2 = {
            "id": "inc2",
            "type": "low_coverage_implication",
            "implication": {"id": "imp2"},
            "details": {"coverage_gap": 0.1},
        }

        self.handler.handle_incident(incident1, self.mock_state)
        self.handler.handle_incident(incident2, self.mock_state)

        stats = self.handler.get_incident_stats()
        assert stats["total_incidents"] == 2
        assert stats["total_rules_generated"] == 2
        assert "LowNovelty" in stats["fail_reason_counts"]
        assert "LowCoverage" in stats["fail_reason_counts"]


class TestIncidentHandlerAcceptanceCriteria:
    """Test incident handler acceptance criteria."""

    def test_incident_to_rule_transformation(self):
        """Test that 1 rejection triggers handler → K↑ and replanning."""
        handler = IncidentHandler()
        state = {"H": {}, "E": {}, "K": {}}

        # Create a rejection incident
        incident = {
            "id": "rejection_inc1",
            "type": "low_coverage_implication",
            "implication": {
                "id": "imp_rejected",
                "premises": ["A"],
                "conclusions": ["B"],
            },
            "details": {"coverage_gap": 0.2},
        }

        # Handle incident
        result = handler.handle_incident(incident, state)

        # Check that K was updated (K↑)
        updated_state = result["updated_state"]
        assert len(updated_state["K"]) > len(state["K"])

        # Check that replanning is required
        assert result["replanning_required"] is True

        # Check that rule was generated
        generated_rule = result["generated_rule"]
        assert generated_rule["type"] == "incident_generated_rule"
        assert generated_rule["incident_id"] == "rejection_inc1"

        # Check that transformation was journaled
        assert len(handler.incident_history) == 1
        assert len(handler.rule_generations) == 1

        print("✅ Incident Handler Acceptance Criteria Met:")
        print(f"   - K updated: {len(updated_state['K'])} rules")
        print(f"   - Replanning required: {result['replanning_required']}")
        print(f"   - Transformation journaled: {len(handler.incident_history)} incidents")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

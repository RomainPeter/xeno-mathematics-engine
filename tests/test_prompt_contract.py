"""
Tests for PromptContract++ system.
"""

import pytest

# Import our modules
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.contracts import (
    PromptContractManager,
    PromptTemplateManager,
    create_ae_implications_contract,
    create_ae_counterexamples_contract,
    create_cegis_choreographies_contract,
)


class TestPromptContractManager:
    """Test PromptContractManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = PromptContractManager()

    def test_create_contract(self):
        """Test creating a prompt contract."""
        goal = "test_goal"
        k = 5
        diversity_keys = ["key1", "key2"]
        hard_constraints = ["constraint1", "constraint2"]
        output_contract = {"fields": ["field1", "field2"]}

        contract = self.manager.create_contract(
            goal, k, diversity_keys, hard_constraints, output_contract
        )

        assert contract.goal == goal
        assert contract.k == k
        assert contract.diversity_keys == diversity_keys
        assert contract.hard_constraints == hard_constraints
        assert contract.output_contract == output_contract
        assert len(contract.prompt_hash) == 16
        assert isinstance(contract.seed, int)
        assert contract.id in self.manager.contracts

    def test_validate_output_valid(self):
        """Test validating valid output."""
        # Create contract
        contract = self.manager.create_contract(
            goal="test",
            k=1,
            diversity_keys=["key1"],
            hard_constraints=["must be valid"],
            output_contract={"fields": ["field1", "diversity_key"]},
        )

        # Valid output
        output = {"field1": "value1", "diversity_key": "key1", "valid": True}

        is_valid, errors = self.manager.validate_output(contract.id, output)

        assert is_valid
        assert len(errors) == 0

    def test_validate_output_invalid(self):
        """Test validating invalid output."""
        # Create contract
        contract = self.manager.create_contract(
            goal="test",
            k=1,
            diversity_keys=["key1"],
            hard_constraints=["must be valid"],
            output_contract={"fields": ["field1", "diversity_key"]},
        )

        # Invalid output - missing required field
        output = {
            "diversity_key": "key1"
            # Missing "field1"
        }

        is_valid, errors = self.manager.validate_output(contract.id, output)

        assert not is_valid
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)

    def test_validate_output_invalid_diversity_key(self):
        """Test validating output with invalid diversity key."""
        # Create contract
        contract = self.manager.create_contract(
            goal="test",
            k=1,
            diversity_keys=["key1"],
            hard_constraints=[],
            output_contract={"fields": ["diversity_key"]},
        )

        # Invalid diversity key
        output = {"diversity_key": "invalid_key"}

        is_valid, errors = self.manager.validate_output(contract.id, output)

        assert not is_valid
        assert any("Invalid diversity_key" in error for error in errors)

    def test_get_contract(self):
        """Test getting a contract."""
        contract = self.manager.create_contract(
            goal="test", k=1, diversity_keys=[], hard_constraints=[], output_contract={}
        )

        retrieved = self.manager.get_contract(contract.id)

        assert retrieved is not None
        assert retrieved.id == contract.id
        assert retrieved.goal == contract.goal

    def test_get_prompt_history(self):
        """Test getting prompt history."""
        # Create some contracts
        self.manager.create_contract("goal1", 1, [], [], {})
        self.manager.create_contract("goal2", 2, [], [], {})

        history = self.manager.get_prompt_history()

        assert len(history) == 2
        assert all("contract_id" in entry for entry in history)
        assert all("prompt_hash" in entry for entry in history)
        assert all("timestamp" in entry for entry in history)

    def test_get_validation_stats(self):
        """Test getting validation statistics."""
        # Create contract and validate
        contract = self.manager.create_contract("test", 1, [], [], {"fields": []})
        self.manager.validate_output(contract.id, {})

        stats = self.manager.get_validation_stats()

        assert "total_contracts" in stats
        assert "total_validations" in stats
        assert "valid_count" in stats
        assert "invalid_count" in stats
        assert "validation_rate" in stats
        assert "seed_registry_size" in stats


class TestPromptTemplateManager:
    """Test PromptTemplateManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template_manager = PromptTemplateManager()
        self.contract_manager = PromptContractManager()

    def test_load_templates(self):
        """Test template loading."""
        templates = self.template_manager.list_templates()

        assert "ae_implications" in templates
        assert "ae_counterexamples" in templates
        assert "cegis_choreographies" in templates

    def test_get_template(self):
        """Test getting a template."""
        template = self.template_manager.get_template("ae_implications")

        assert template is not None
        assert template["goal"] == "propose_implications"
        assert template["k"] == 8
        assert "diversity_keys" in template
        assert "hard_constraints" in template
        assert "output_contract" in template

    def test_create_contract_from_template(self):
        """Test creating contract from template."""
        contract = self.template_manager.create_contract_from_template(
            "ae_implications", self.contract_manager
        )

        assert contract is not None
        assert contract.goal == "propose_implications"
        assert contract.k == 8
        assert "attributes" in contract.diversity_keys
        assert "clause_type" in contract.diversity_keys

    def test_create_contract_from_nonexistent_template(self):
        """Test creating contract from nonexistent template."""
        contract = self.template_manager.create_contract_from_template(
            "nonexistent", self.contract_manager
        )

        assert contract is None


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_ae_implications_contract(self):
        """Test creating AE implications contract."""
        contract = create_ae_implications_contract()

        assert contract is not None
        assert contract.goal == "propose_implications"
        assert contract.k == 8
        assert "attributes" in contract.diversity_keys

    def test_create_ae_counterexamples_contract(self):
        """Test creating AE counterexamples contract."""
        contract = create_ae_counterexamples_contract()

        assert contract is not None
        assert contract.goal == "propose_counterexamples"
        assert contract.k == 1
        assert "violation_type" in contract.diversity_keys

    def test_create_cegis_choreographies_contract(self):
        """Test creating CEGIS choreographies contract."""
        contract = create_cegis_choreographies_contract()

        assert contract is not None
        assert contract.goal == "synthesize_choreography"
        assert contract.k == 3
        assert "operation_sequence" in contract.diversity_keys


class TestPromptContractAcceptanceCriteria:
    """Test PromptContract++ acceptance criteria."""

    def test_k_structured_propositions(self):
        """Test k structured propositions conforming to contract."""
        contract = create_ae_implications_contract()

        # Mock structured propositions
        propositions = []
        for i in range(contract.k):
            proposition = {
                "premises": [f"premise_{i}"],
                "conclusion": f"conclusion_{i}",
                "justification": f"justification_{i}",
                "diversity_key": "attributes" if i % 2 == 0 else "clause_type",
            }
            propositions.append(proposition)

        # Validate each proposition
        manager = PromptContractManager()
        all_valid = True
        for proposition in propositions:
            is_valid, errors = manager.validate_output(contract.id, proposition)
            if not is_valid:
                all_valid = False
                print(f"Invalid proposition: {errors}")

        assert all_valid, "All propositions should be valid"

    def test_diversity_keys_present(self):
        """Test that diversity_keys are present in output."""
        contract = create_ae_implications_contract()

        # Mock output with diversity keys
        output = {
            "premises": ["A"],
            "conclusion": "B",
            "justification": "test",
            "diversity_key": "attributes",
        }

        manager = PromptContractManager()
        is_valid, errors = manager.validate_output(contract.id, output)

        assert is_valid
        assert "diversity_key" in output
        assert output["diversity_key"] in contract.diversity_keys

    def test_prompt_hash_journaled(self):
        """Test that prompt_hash is journaled."""
        contract = create_ae_implications_contract()

        # Check that prompt hash is stored
        assert contract.prompt_hash is not None
        assert len(contract.prompt_hash) == 16

        # Check that it's in prompt history
        manager = PromptContractManager()
        history = manager.get_prompt_history()

        # Find our contract in history
        contract_in_history = any(entry["contract_id"] == contract.id for entry in history)
        assert contract_in_history

        print("✅ PromptContract++ Acceptance Criteria Met:")
        print(f"   - k structured propositions: {contract.k}")
        print(f"   - diversity_keys present: {contract.diversity_keys}")
        print(f"   - prompt_hash journaled: {contract.prompt_hash}")
        print(f"   - seed generated: {contract.seed}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

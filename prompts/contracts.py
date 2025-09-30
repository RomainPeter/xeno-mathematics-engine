"""
PromptContract++ for Discovery Engine 2-Cat.
Implements prompt governance with hash, seeds, and output validation.
"""

import hashlib
import json
import random
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptContract:
    """Represents a prompt contract with governance."""

    id: str
    goal: str
    k: int
    diversity_keys: List[str]
    hard_constraints: List[str]
    output_contract: Dict[str, Any]
    prompt_hash: str
    seed: int
    timestamp: str


class PromptContractManager:
    """Manages PromptContract++ system."""

    def __init__(self):
        self.contracts = {}
        self.prompt_history = []
        self.seed_registry = {}
        self.output_validations = {}

    def create_contract(
        self,
        goal: str,
        k: int,
        diversity_keys: List[str],
        hard_constraints: List[str],
        output_contract: Dict[str, Any],
    ) -> PromptContract:
        """Create a new prompt contract."""
        contract_id = f"contract_{len(self.contracts) + 1}_{int(time.time())}"

        # Generate prompt content
        prompt_content = self._generate_prompt_content(goal, k, diversity_keys, hard_constraints)

        # Calculate prompt hash
        prompt_hash = self._calculate_prompt_hash(prompt_content)

        # Generate seed
        seed = self._generate_seed()

        # Create contract
        contract = PromptContract(
            id=contract_id,
            goal=goal,
            k=k,
            diversity_keys=diversity_keys,
            hard_constraints=hard_constraints,
            output_contract=output_contract,
            prompt_hash=prompt_hash,
            seed=seed,
            timestamp=datetime.now().isoformat(),
        )

        # Store contract
        self.contracts[contract_id] = contract
        self.prompt_history.append(
            {
                "contract_id": contract_id,
                "prompt_hash": prompt_hash,
                "timestamp": contract.timestamp,
            }
        )

        return contract

    def _generate_prompt_content(
        self, goal: str, k: int, diversity_keys: List[str], hard_constraints: List[str]
    ) -> str:
        """Generate prompt content."""
        prompt = f"""
Goal: {goal}
Generate {k} diverse items with the following diversity keys: {', '.join(diversity_keys)}
Hard constraints: {', '.join(hard_constraints)}

Please provide structured output with the following fields:
- premises: List of premises
- conclusions: List of conclusions  
- justification: Explanation
- diversity_key: One of {diversity_keys}
"""
        return prompt.strip()

    def _calculate_prompt_hash(self, prompt_content: str) -> str:
        """Calculate hash for prompt content."""
        return hashlib.sha256(prompt_content.encode("utf-8")).hexdigest()[:16]

    def _generate_seed(self) -> int:
        """Generate a seed for reproducibility."""
        seed = random.randint(1000000, 9999999)
        self.seed_registry[seed] = {
            "timestamp": datetime.now().isoformat(),
            "used": False,
        }
        return seed

    def validate_output(self, contract_id: str, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate output against contract."""
        if contract_id not in self.contracts:
            return False, ["Contract not found"]

        contract = self.contracts[contract_id]
        errors = []

        # Check required fields
        required_fields = contract.output_contract.get("fields", [])
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")

        # Check diversity keys
        if "diversity_key" in output:
            if output["diversity_key"] not in contract.diversity_keys:
                errors.append(f"Invalid diversity_key: {output['diversity_key']}")

        # Check hard constraints
        for constraint in contract.hard_constraints:
            if not self._check_constraint(constraint, output):
                errors.append(f"Hard constraint violated: {constraint}")

        # Check k items
        if isinstance(output, list) and len(output) != contract.k:
            errors.append(f"Expected {contract.k} items, got {len(output)}")

        is_valid = len(errors) == 0

        # Store validation result
        self.output_validations[contract_id] = {
            "valid": is_valid,
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "output_hash": self._calculate_prompt_hash(json.dumps(output, sort_keys=True)),
        }

        return is_valid, errors

    def _check_constraint(self, constraint: str, output: Dict[str, Any]) -> bool:
        """Check if a hard constraint is satisfied."""
        # Mock constraint checking
        if "respect obligations K" in constraint:
            return "obligations" in output or "K" in str(output)
        elif "must be valid" in constraint:
            return "valid" in output or "valid" in str(output)
        else:
            return True  # Assume satisfied for demo

    def get_contract(self, contract_id: str) -> Optional[PromptContract]:
        """Get a contract by ID."""
        return self.contracts.get(contract_id)

    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """Get prompt history."""
        return self.prompt_history.copy()

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        total_validations = len(self.output_validations)
        valid_count = sum(1 for v in self.output_validations.values() if v["valid"])

        return {
            "total_contracts": len(self.contracts),
            "total_validations": total_validations,
            "valid_count": valid_count,
            "invalid_count": total_validations - valid_count,
            "validation_rate": (valid_count / total_validations if total_validations > 0 else 0),
            "seed_registry_size": len(self.seed_registry),
        }


class PromptTemplateManager:
    """Manages prompt templates."""

    def __init__(self):
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load prompt templates."""
        # AE Implications template
        self.templates["ae_implications"] = {
            "goal": "propose_implications",
            "k": 8,
            "diversity_keys": ["attributes", "clause_type"],
            "hard_constraints": ["must respect obligations K"],
            "output_contract": {
                "fields": ["premises", "conclusion", "justification", "diversity_key"]
            },
        }

        # AE Counterexamples template
        self.templates["ae_counterexamples"] = {
            "goal": "propose_counterexamples",
            "k": 1,
            "diversity_keys": ["violation_type", "severity"],
            "hard_constraints": ["must refute implication"],
            "output_contract": {
                "fields": ["refuted_implication", "counterexample_data", "evidence"]
            },
        }

        # CEGIS Choreographies template
        self.templates["cegis_choreographies"] = {
            "goal": "synthesize_choreography",
            "k": 3,
            "diversity_keys": ["operation_sequence", "parallel_execution"],
            "hard_constraints": ["must satisfy post-conditions", "respect budget V"],
            "output_contract": {
                "fields": [
                    "operations",
                    "pre_conditions",
                    "post_conditions",
                    "guards",
                    "budget",
                    "diversity_key",
                ]
            },
        }

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a prompt template."""
        return self.templates.get(template_name)

    def create_contract_from_template(
        self, template_name: str, contract_manager: PromptContractManager
    ) -> Optional[PromptContract]:
        """Create a contract from a template."""
        template = self.get_template(template_name)
        if not template:
            return None

        return contract_manager.create_contract(
            goal=template["goal"],
            k=template["k"],
            diversity_keys=template["diversity_keys"],
            hard_constraints=template["hard_constraints"],
            output_contract=template["output_contract"],
        )

    def list_templates(self) -> List[str]:
        """List available templates."""
        return list(self.templates.keys())


# Global instances
prompt_contract_manager = PromptContractManager()
template_manager = PromptTemplateManager()


def create_ae_implications_contract() -> PromptContract:
    """Create AE implications contract from template."""
    return template_manager.create_contract_from_template(
        "ae_implications", prompt_contract_manager
    )


def create_ae_counterexamples_contract() -> PromptContract:
    """Create AE counterexamples contract from template."""
    return template_manager.create_contract_from_template(
        "ae_counterexamples", prompt_contract_manager
    )


def create_cegis_choreographies_contract() -> PromptContract:
    """Create CEGIS choreographies contract from template."""
    return template_manager.create_contract_from_template(
        "cegis_choreographies", prompt_contract_manager
    )

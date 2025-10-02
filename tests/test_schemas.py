"""
Tests for JSON schemas validation.
"""

import json
from pathlib import Path

import jsonschema


class TestSchemaValidation:
    """Test cases for schema validation."""

    def test_domain_spec_schema(self):
        """Test DomainSpec schema validation."""
        schema_path = Path("schemas/DomainSpec.json")
        example_path = Path("schemas/examples/regtech_domain_spec.json")

        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Load example
        with open(example_path, "r") as f:
            example = json.load(f)

        # Validate
        jsonschema.validate(example, schema)
        print("✅ DomainSpec schema validation passed")

    def test_composite_op_schema(self):
        """Test CompositeOp schema validation."""
        schema_path = Path("schemas/CompositeOp.json")

        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Create test example
        example = {
            "id": "test_composite",
            "operations": [
                {
                    "id": "op1",
                    "type": "validate",
                    "preconditions": ["input_available"],
                    "postconditions": ["validated"],
                }
            ],
            "preconditions": ["system_ready"],
            "postconditions": ["operation_complete"],
        }

        # Validate
        jsonschema.validate(example, schema)
        print("✅ CompositeOp schema validation passed")

    def test_dca_schema(self):
        """Test DCA schema validation."""
        schema_path = Path("schemas/DCA.json")

        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Create test example
        example = {
            "id": "dca_001",
            "type": "ae_query",
            "context": {"domain": "regtech"},
            "verdict": "accept",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        # Validate
        jsonschema.validate(example, schema)
        print("✅ DCA schema validation passed")

    def test_v_schema(self):
        """Test V (cost vector) schema validation."""
        schema_path = Path("schemas/V.json")

        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Create test example
        example = {
            "time_ms": 1000,
            "audit_cost": 50.0,
            "legal_risk": 0.3,
            "tech_debt": 0.2,
            "novelty": 0.8,
            "coverage": 0.7,
        }

        # Validate
        jsonschema.validate(example, schema)
        print("✅ V schema validation passed")

    def test_fail_reason_schema(self):
        """Test FailReason schema validation."""
        schema_path = Path("schemas/FailReason.json")

        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Create test example
        example = {
            "code": "LowNovelty",
            "severity": "medium",
            "context": {"novelty_score": 0.1},
            "handler": "egraph_add_equiv_forbidden",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        # Validate
        jsonschema.validate(example, schema)
        print("✅ FailReason schema validation passed")


if __name__ == "__main__":
    # Run tests directly
    import sys

    sys.path.insert(0, ".")

    print("Running Schema Validation Tests...")

    try:
        test = TestSchemaValidation()
        test.test_domain_spec_schema()
        test.test_composite_op_schema()
        test.test_dca_schema()
        test.test_v_schema()
        test.test_fail_reason_schema()
        print("✅ All schema validation tests passed!")
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")

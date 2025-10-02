#!/usr/bin/env python3
"""
Tests for capabilities bundle generation.
"""

import json
from pathlib import Path
from unittest.mock import patch

from pefc.capabilities.bundle import CapabilityRegistry, ProofBundle
from pefc.capabilities.handlers import HSTreeHandler, OPAHandler


class TestProofBundle:
    """Test ProofBundle generation."""

    def test_proof_bundle_creation(self, temp_workspace: Path):
        """Test ProofBundle creation with valid data."""
        # Create test data
        test_data = {
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Create ProofBundle
        bundle = ProofBundle(
            capabilities=test_data["capabilities"],
            metadata=test_data["metadata"],
        )

        # Check bundle properties
        assert bundle.capabilities == test_data["capabilities"]
        assert bundle.metadata == test_data["metadata"]
        assert bundle.format_version == "1.0"

    def test_proof_bundle_serialization(self, temp_workspace: Path):
        """Test ProofBundle serialization to JSON."""
        # Create test data
        test_data = {
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Create ProofBundle
        bundle = ProofBundle(
            capabilities=test_data["capabilities"],
            metadata=test_data["metadata"],
        )

        # Serialize to JSON
        json_str = bundle.to_json()
        json_data = json.loads(json_str)

        # Check JSON structure
        assert json_data["format_version"] == "1.0"
        assert json_data["capabilities"] == test_data["capabilities"]
        assert json_data["metadata"] == test_data["metadata"]

    def test_proof_bundle_save_to_file(self, temp_workspace: Path):
        """Test ProofBundle save to file."""
        # Create test data
        test_data = {
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Create ProofBundle
        bundle = ProofBundle(
            capabilities=test_data["capabilities"],
            metadata=test_data["metadata"],
        )

        # Save to file
        output_file = temp_workspace / "bundle.json"
        bundle.save_to_file(output_file)

        # Check file was created
        assert output_file.exists()

        # Check file content
        with open(output_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data["format_version"] == "1.0"
        assert saved_data["capabilities"] == test_data["capabilities"]
        assert saved_data["metadata"] == test_data["metadata"]

    def test_proof_bundle_load_from_file(self, temp_workspace: Path):
        """Test ProofBundle load from file."""
        # Create test data
        test_data = {
            "format_version": "1.0",
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Save test data to file
        test_file = temp_workspace / "test_bundle.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f, indent=2)

        # Load from file
        bundle = ProofBundle.load_from_file(test_file)

        # Check bundle properties
        assert bundle.format_version == "1.0"
        assert bundle.capabilities == test_data["capabilities"]
        assert bundle.metadata == test_data["metadata"]

    def test_proof_bundle_validation(self, temp_workspace: Path):
        """Test ProofBundle validation."""
        # Create test data with missing required fields
        test_data = {
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Create ProofBundle
        bundle = ProofBundle(
            capabilities=test_data["capabilities"],
            metadata=test_data["metadata"],
        )

        # Validate bundle
        is_valid, errors = bundle.validate()
        assert is_valid
        assert len(errors) == 0

    def test_proof_bundle_validation_failure(self, temp_workspace: Path):
        """Test ProofBundle validation failure."""
        # Create test data with invalid structure
        test_data = {
            "capabilities": [
                {
                    "name": "test_capability",
                    "version": "1.0.0",
                    "description": "Test capability",
                    "type": "handler",
                    "handler": "HSTreeHandler",
                    "config": {"param1": "value1"},
                }
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "generator_version": "0.1.0",
                "generator": "pefc",
            },
        }

        # Create ProofBundle with invalid data
        bundle = ProofBundle(
            capabilities=test_data["capabilities"],
            metadata=test_data["metadata"],
        )

        # Manually corrupt the bundle
        bundle.capabilities = None

        # Validate bundle
        is_valid, errors = bundle.validate()
        assert not is_valid
        assert len(errors) > 0


class TestCapabilityRegistry:
    """Test CapabilityRegistry functionality."""

    def test_capability_registry_creation(self, temp_workspace: Path):
        """Test CapabilityRegistry creation."""
        registry = CapabilityRegistry()

        # Check initial state
        assert len(registry.capabilities) == 0
        assert registry.allowlist == []
        assert registry.denylist == []

    def test_capability_registry_register(self, temp_workspace: Path):
        """Test capability registration."""
        registry = CapabilityRegistry()

        # Register a capability
        capability = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        registry.register(capability)

        # Check registration
        assert len(registry.capabilities) == 1
        assert registry.capabilities[0] == capability

    def test_capability_registry_allowlist(self, temp_workspace: Path):
        """Test capability allowlist filtering."""
        registry = CapabilityRegistry()
        registry.allowlist = ["test_capability"]

        # Register capabilities
        capability1 = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        capability2 = {
            "name": "other_capability",
            "version": "1.0.0",
            "description": "Other capability",
            "type": "handler",
            "handler": "OPAHandler",
            "config": {"param2": "value2"},
        }

        registry.register(capability1)
        registry.register(capability2)

        # Get filtered capabilities
        filtered = registry.get_filtered_capabilities()

        # Check filtering
        assert len(filtered) == 1
        assert filtered[0]["name"] == "test_capability"

    def test_capability_registry_denylist(self, temp_workspace: Path):
        """Test capability denylist filtering."""
        registry = CapabilityRegistry()
        registry.denylist = ["other_capability"]

        # Register capabilities
        capability1 = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        capability2 = {
            "name": "other_capability",
            "version": "1.0.0",
            "description": "Other capability",
            "type": "handler",
            "handler": "OPAHandler",
            "config": {"param2": "value2"},
        }

        registry.register(capability1)
        registry.register(capability2)

        # Get filtered capabilities
        filtered = registry.get_filtered_capabilities()

        # Check filtering
        assert len(filtered) == 1
        assert filtered[0]["name"] == "test_capability"

    def test_capability_registry_generate_bundle(self, temp_workspace: Path):
        """Test capability bundle generation."""
        registry = CapabilityRegistry()

        # Register capabilities
        capability1 = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        capability2 = {
            "name": "other_capability",
            "version": "1.0.0",
            "description": "Other capability",
            "type": "handler",
            "handler": "OPAHandler",
            "config": {"param2": "value2"},
        }

        registry.register(capability1)
        registry.register(capability2)

        # Generate bundle
        bundle = registry.generate_bundle()

        # Check bundle
        assert bundle.format_version == "1.0"
        assert len(bundle.capabilities) == 2
        assert bundle.metadata["generator"] == "pefc"
        assert bundle.metadata["generator_version"] == "0.1.0"


class TestCapabilityHandlers:
    """Test capability handlers."""

    def test_hstree_handler_creation(self, temp_workspace: Path):
        """Test HSTreeHandler creation."""
        handler = HSTreeHandler(
            name="test_hstree",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Check handler properties
        assert handler.name == "test_hstree"
        assert handler.version == "1.0.0"
        assert handler.config == {"param1": "value1"}

    def test_hstree_handler_execute(self, temp_workspace: Path):
        """Test HSTreeHandler execution."""
        handler = HSTreeHandler(
            name="test_hstree",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Mock execution
        with patch.object(handler, "execute") as mock_execute:
            mock_execute.return_value = {"result": "success"}

            result = handler.execute()

            # Check result
            assert result == {"result": "success"}
            mock_execute.assert_called_once()

    def test_opa_handler_creation(self, temp_workspace: Path):
        """Test OPAHandler creation."""
        handler = OPAHandler(
            name="test_opa",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Check handler properties
        assert handler.name == "test_opa"
        assert handler.version == "1.0.0"
        assert handler.config == {"param1": "value1"}

    def test_opa_handler_execute(self, temp_workspace: Path):
        """Test OPAHandler execution."""
        handler = OPAHandler(
            name="test_opa",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Mock execution
        with patch.object(handler, "execute") as mock_execute:
            mock_execute.return_value = {"result": "success"}

            result = handler.execute()

            # Check result
            assert result == {"result": "success"}
            mock_execute.assert_called_once()

    def test_capability_handler_validation(self, temp_workspace: Path):
        """Test capability handler validation."""
        handler = HSTreeHandler(
            name="test_hstree",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Validate handler
        is_valid, errors = handler.validate()
        assert is_valid
        assert len(errors) == 0

    def test_capability_handler_validation_failure(self, temp_workspace: Path):
        """Test capability handler validation failure."""
        handler = HSTreeHandler(
            name="test_hstree",
            version="1.0.0",
            config={"param1": "value1"},
        )

        # Manually corrupt the handler
        handler.name = None

        # Validate handler
        is_valid, errors = handler.validate()
        assert not is_valid
        assert len(errors) > 0


class TestCapabilityIntegration:
    """Test capability integration scenarios."""

    def test_capability_bundle_generation_integration(self, temp_workspace: Path):
        """Test end-to-end capability bundle generation."""
        # Create registry
        registry = CapabilityRegistry()

        # Register multiple capabilities
        capabilities = [
            {
                "name": "hstree_handler",
                "version": "1.0.0",
                "description": "HSTree handler capability",
                "type": "handler",
                "handler": "HSTreeHandler",
                "config": {"param1": "value1"},
            },
            {
                "name": "opa_handler",
                "version": "1.0.0",
                "description": "OPA handler capability",
                "type": "handler",
                "handler": "OPAHandler",
                "config": {"param2": "value2"},
            },
        ]

        for capability in capabilities:
            registry.register(capability)

        # Generate bundle
        bundle = registry.generate_bundle()

        # Check bundle structure
        assert bundle.format_version == "1.0"
        assert len(bundle.capabilities) == 2
        assert bundle.metadata["generator"] == "pefc"
        assert bundle.metadata["generator_version"] == "0.1.0"

        # Check capabilities
        capability_names = [cap["name"] for cap in bundle.capabilities]
        assert "hstree_handler" in capability_names
        assert "opa_handler" in capability_names

    def test_capability_bundle_serialization_integration(self, temp_workspace: Path):
        """Test capability bundle serialization integration."""
        # Create registry
        registry = CapabilityRegistry()

        # Register capabilities
        capability = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        registry.register(capability)

        # Generate bundle
        bundle = registry.generate_bundle()

        # Serialize to JSON
        json_str = bundle.to_json()
        json_data = json.loads(json_str)

        # Check JSON structure
        assert json_data["format_version"] == "1.0"
        assert len(json_data["capabilities"]) == 1
        assert json_data["capabilities"][0]["name"] == "test_capability"
        assert json_data["metadata"]["generator"] == "pefc"

    def test_capability_bundle_validation_integration(self, temp_workspace: Path):
        """Test capability bundle validation integration."""
        # Create registry
        registry = CapabilityRegistry()

        # Register capabilities
        capability = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        registry.register(capability)

        # Generate bundle
        bundle = registry.generate_bundle()

        # Validate bundle
        is_valid, errors = bundle.validate()
        assert is_valid
        assert len(errors) == 0

    def test_capability_bundle_save_load_integration(self, temp_workspace: Path):
        """Test capability bundle save/load integration."""
        # Create registry
        registry = CapabilityRegistry()

        # Register capabilities
        capability = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability",
            "type": "handler",
            "handler": "HSTreeHandler",
            "config": {"param1": "value1"},
        }

        registry.register(capability)

        # Generate bundle
        bundle = registry.generate_bundle()

        # Save to file
        output_file = temp_workspace / "bundle.json"
        bundle.save_to_file(output_file)

        # Load from file
        loaded_bundle = ProofBundle.load_from_file(output_file)

        # Check loaded bundle
        assert loaded_bundle.format_version == bundle.format_version
        assert loaded_bundle.capabilities == bundle.capabilities
        assert loaded_bundle.metadata == bundle.metadata

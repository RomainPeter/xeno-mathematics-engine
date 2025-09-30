#!/usr/bin/env python3
"""
Tests for HS-Tree minimal test generation
Tests the HS-Tree algorithm for generating minimal test cases from constraint breaches
"""
import pytest
import json
import tempfile
from pathlib import Path
from methods.hstree.minimal_tests import HSTreeMinimalTests


class TestHSTree:
    """Test HS-Tree minimal test generation."""

    def setup_method(self):
        """Setup test environment."""
        self.hstree = HSTreeMinimalTests()

    def test_add_constraint_violation(self):
        """Test adding constraint violations to knowledge base."""
        violation = {
            "id": "violation_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package", "version": "1.0.0"},
            "severity": "high",
        }

        self.hstree.add_constraint_violation(violation)

        assert len(self.hstree.constraint_violations) == 1
        assert "violation_1" in self.hstree.knowledge_base
        assert (
            self.hstree.knowledge_base["violation_1"]["constraint_type"]
            == "semver_violation"
        )

    def test_generate_semver_tests(self):
        """Test generation of semver violation tests."""
        incident = {
            "id": "semver_breach_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package", "version": "2.1.0"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        assert len(tests) >= 2, "Should generate at least 2 semver tests"

        # Check test categories
        categories = [tc.category for tc in tests]
        assert "semver" in categories, "Should include semver category tests"

        # Check test priorities
        priorities = [tc.priority for tc in tests]
        assert 1 in priorities, "Should include high priority tests"

    def test_generate_license_tests(self):
        """Test generation of license violation tests."""
        incident = {
            "id": "license_breach_1",
            "constraint_type": "license_violation",
            "context": {"package": "test-package", "license": "AGPL-3.0"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        assert len(tests) >= 1, "Should generate at least 1 license test"

        # Check test categories
        categories = [tc.category for tc in tests]
        assert "license" in categories, "Should include license category tests"

    def test_generate_security_tests(self):
        """Test generation of security violation tests."""
        incident = {
            "id": "security_breach_1",
            "constraint_type": "security_violation",
            "context": {"file_path": "test.py", "content": "password = 'secret'"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        assert len(tests) >= 1, "Should generate at least 1 security test"

        # Check test categories
        categories = [tc.category for tc in tests]
        assert "security" in categories, "Should include security category tests"

    def test_generate_pii_tests(self):
        """Test generation of PII violation tests."""
        incident = {
            "id": "pii_breach_1",
            "constraint_type": "pii_violation",
            "context": {"file_path": "test.py", "content": "user@example.com"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        assert len(tests) >= 1, "Should generate at least 1 PII test"

        # Check test categories
        categories = [tc.category for tc in tests]
        assert "pii" in categories, "Should include PII category tests"

    def test_generate_generic_tests(self):
        """Test generation of generic tests."""
        incident = {
            "id": "generic_breach_1",
            "constraint_type": "unknown_violation",
            "context": {"some_field": "some_value"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        assert len(tests) >= 1, "Should generate at least 1 generic test"

        # Check test categories
        categories = [tc.category for tc in tests]
        assert "generic" in categories, "Should include generic category tests"

    def test_test_case_structure(self):
        """Test that generated test cases have correct structure."""
        incident = {
            "id": "test_breach_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        for tc in tests:
            assert hasattr(tc, "id"), "Test case should have id"
            assert hasattr(tc, "description"), "Test case should have description"
            assert hasattr(tc, "input_data"), "Test case should have input_data"
            assert hasattr(
                tc, "expected_output"
            ), "Test case should have expected_output"
            assert hasattr(tc, "constraints"), "Test case should have constraints"
            assert hasattr(tc, "priority"), "Test case should have priority"
            assert hasattr(tc, "category"), "Test case should have category"

            assert isinstance(tc.id, str), "ID should be string"
            assert isinstance(tc.description, str), "Description should be string"
            assert isinstance(tc.input_data, dict), "Input data should be dict"
            assert isinstance(
                tc.expected_output, dict
            ), "Expected output should be dict"
            assert isinstance(tc.constraints, list), "Constraints should be list"
            assert isinstance(tc.priority, int), "Priority should be int"
            assert isinstance(tc.category, str), "Category should be string"

    def test_get_minimal_test_suite(self):
        """Test getting complete test suite."""
        # Add some test cases
        incident1 = {
            "id": "breach_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package"},
        }
        incident2 = {
            "id": "breach_2",
            "constraint_type": "license_violation",
            "context": {"package": "test-package"},
        }

        self.hstree.generate_minimal_tests(incident1)
        self.hstree.generate_minimal_tests(incident2)

        test_suite = self.hstree.get_minimal_test_suite()

        assert "version" in test_suite, "Should include version"
        assert "generated_at" in test_suite, "Should include generation timestamp"
        assert "total_tests" in test_suite, "Should include total tests count"
        assert "test_cases" in test_suite, "Should include test cases"
        assert (
            "constraint_violations" in test_suite
        ), "Should include constraint violations count"
        assert "knowledge_base_size" in test_suite, "Should include knowledge base size"

        assert test_suite["total_tests"] > 0, "Should have generated tests"
        assert len(test_suite["test_cases"]) > 0, "Should have test cases"

    def test_export_tests(self):
        """Test exporting tests to file."""
        # Add some test cases
        incident = {
            "id": "export_breach_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package"},
        }

        self.hstree.generate_minimal_tests(incident)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            success = self.hstree.export_tests(output_file)

            assert success, "Export should succeed"
            assert Path(output_file).exists(), "Output file should exist"

            # Verify file contents
            with open(output_file) as f:
                exported_data = json.load(f)

            assert (
                "total_tests" in exported_data
            ), "Exported data should include total_tests"
            assert exported_data["total_tests"] > 0, "Should have exported tests"

        finally:
            Path(output_file).unlink()

    def test_get_stats(self):
        """Test getting HS-Tree statistics."""
        # Add some test cases
        incidents = [
            {"id": "stats_1", "constraint_type": "semver_violation", "context": {}},
            {"id": "stats_2", "constraint_type": "license_violation", "context": {}},
            {"id": "stats_3", "constraint_type": "security_violation", "context": {}},
        ]

        for incident in incidents:
            self.hstree.generate_minimal_tests(incident)

        stats = self.hstree.get_stats()

        assert "total_tests" in stats, "Should include total tests"
        assert "categories" in stats, "Should include categories breakdown"
        assert (
            "constraint_violations" in stats
        ), "Should include constraint violations count"
        assert "knowledge_base_size" in stats, "Should include knowledge base size"
        assert "avg_priority" in stats, "Should include average priority"

        assert stats["total_tests"] > 0, "Should have generated tests"
        assert len(stats["categories"]) > 0, "Should have categories"

    def test_multiple_violations(self):
        """Test handling multiple constraint violations."""
        violations = [
            {"id": "multi_1", "constraint_type": "semver_violation", "context": {}},
            {"id": "multi_2", "constraint_type": "license_violation", "context": {}},
            {"id": "multi_3", "constraint_type": "security_violation", "context": {}},
        ]

        for violation in violations:
            self.hstree.add_constraint_violation(violation)
            self.hstree.generate_minimal_tests(violation)

        assert len(self.hstree.constraint_violations) == 3, "Should have 3 violations"
        assert len(self.hstree.test_cases) > 0, "Should have generated test cases"
        assert (
            len(self.hstree.knowledge_base) == 3
        ), "Should have 3 knowledge base entries"

    def test_test_priority_distribution(self):
        """Test that test priorities are distributed correctly."""
        incident = {
            "id": "priority_test_1",
            "constraint_type": "semver_violation",
            "context": {"package": "test-package"},
        }

        tests = self.hstree.generate_minimal_tests(incident)

        priorities = [tc.priority for tc in tests]

        # Should have different priority levels
        assert len(set(priorities)) > 1, "Should have multiple priority levels"

        # Priority 1 should be most important
        assert 1 in priorities, "Should have priority 1 tests"

        # All priorities should be positive
        assert all(p > 0 for p in priorities), "All priorities should be positive"

    def test_test_category_distribution(self):
        """Test that test categories are distributed correctly."""
        incidents = [
            {"id": "cat_1", "constraint_type": "semver_violation", "context": {}},
            {"id": "cat_2", "constraint_type": "license_violation", "context": {}},
            {"id": "cat_3", "constraint_type": "security_violation", "context": {}},
        ]

        for incident in incidents:
            self.hstree.generate_minimal_tests(incident)

        categories = [tc.category for tc in self.hstree.test_cases]

        # Should have multiple categories
        assert len(set(categories)) > 1, "Should have multiple categories"

        # Should include expected categories
        expected_categories = ["semver", "license", "security"]
        for expected in expected_categories:
            assert expected in categories, f"Should include {expected} category"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

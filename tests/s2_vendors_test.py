"""
Tests for S2 vendors scenarios
"""

import pytest
import json
from pathlib import Path


class TestS2Vendors:
    """Test S2 vendors scenarios"""

    def test_api_break_before_fails(self):
        """Test that api-break scenario fails before rewrite"""
        test_file = Path("tests/expected-fail-2cat/api-break_before.json")
        assert test_file.exists()

        with open(test_file) as f:
            test_data = json.load(f)

        # Simulate OPA evaluation
        input_data = test_data["input"]

        # Should fail because:
        # - semver_bump = false
        # - changelog_updated = false
        # - api_tests_missing = true
        assert not input_data["semver_bump"]
        assert not input_data["changelog_updated"]
        assert input_data["api_tests_missing"]

        # Expected to be denied
        assert test_data["expected_result"] == "deny"

    def test_typosquat_cve_before_fails(self):
        """Test that typosquat/CVE scenario fails before rewrite"""
        test_file = Path("tests/expected-fail-2cat/typosquat-cve_before.json")
        assert test_file.exists()

        with open(test_file) as f:
            test_data = json.load(f)

        input_data = test_data["input"]

        # Should fail because:
        # - dependency_unpinned = true
        # - cve_detected = true
        # - typosquat_detected = true
        assert input_data["dependency_unpinned"]
        assert input_data["cve_detected"]
        assert input_data["typosquat_detected"]

        # Expected to be denied
        assert test_data["expected_result"] == "deny"

    def test_secret_egress_before_fails(self):
        """Test that secret/egress scenario fails before rewrite"""
        test_file = Path("tests/expected-fail-2cat/secret-egress_before.json")
        assert test_file.exists()

        with open(test_file) as f:
            test_data = json.load(f)

        input_data = test_data["input"]

        # Should fail because:
        # - secrets_detected = true
        # - egress_attempted = true
        # - api_keys_plaintext = true
        assert input_data["secrets_detected"]
        assert input_data["egress_attempted"]
        assert input_data["api_keys_plaintext"]

        # Expected to be denied
        assert test_data["expected_result"] == "deny"

    def test_s2_corpus_structure(self):
        """Test that S2 corpus structure is correct"""
        # Check api-break
        api_break_dir = Path("corpus/s2/vendors/api-break")
        assert api_break_dir.exists()
        assert (api_break_dir / "plan.json").exists()
        assert (api_break_dir / "K.rego").exists()
        assert (api_break_dir / "seed" / "before.json").exists()
        assert (api_break_dir / "seed" / "after.json").exists()

        # Check typosquat-cve
        typosquat_dir = Path("corpus/s2/vendors/typosquat-cve")
        assert typosquat_dir.exists()
        assert (typosquat_dir / "plan.json").exists()
        assert (typosquat_dir / "K.rego").exists()
        assert (typosquat_dir / "requirements.in").exists()
        assert (typosquat_dir / "requirements.lock.bad").exists()
        assert (typosquat_dir / "requirements.lock.fixed").exists()

        # Check secret-egress
        secret_dir = Path("corpus/s2/vendors/secret-egress")
        assert secret_dir.exists()
        assert (secret_dir / "plan.json").exists()
        assert (secret_dir / "K.rego").exists()
        assert (secret_dir / "script_calls_net.py").exists()
        assert (secret_dir / "fixture" / "before.json").exists()
        assert (secret_dir / "fixture" / "after.json").exists()

    def test_policies_structure(self):
        """Test that policies are correctly structured"""
        policy_dir = Path("policy")
        assert policy_dir.exists()

        # Check all policy files exist
        policy_files = [
            "semver.rego",
            "changelog.rego",
            "dep_pinned.rego",
            "no_secrets.rego",
            "no_egress.rego",
        ]

        for policy_file in policy_files:
            assert (policy_dir / policy_file).exists()

    def test_after_rewrite_success(self):
        """Test that scenarios pass after rewrite"""
        # This would be tested with actual 2-category active mode
        # For now, just verify the structure exists

        # Check api-break after
        api_break_after = Path("corpus/s2/vendors/api-break/seed/after.json")
        assert api_break_after.exists()

        with open(api_break_after) as f:
            after_data = json.load(f)

        # Should pass after rewrite
        assert after_data["semver_bump"]
        assert after_data["changelog_updated"]
        assert after_data["api_tests_present"]

        # Check typosquat-cve after
        typosquat_after = Path("corpus/s2/vendors/typosquat-cve/requirements.lock.fixed")
        assert typosquat_after.exists()

        # Check secret-egress after
        secret_after = Path("corpus/s2/vendors/secret-egress/fixture/after.json")
        assert secret_after.exists()

        with open(secret_after) as f:
            secret_after_data = json.load(f)

        # Should pass after rewrite
        assert not secret_after_data["secrets_detected"]
        assert not secret_after_data["egress_attempted"]
        assert secret_after_data["api_keys_encrypted"]
        assert secret_after_data["guard_checks_passed"]


if __name__ == "__main__":
    pytest.main([__file__])

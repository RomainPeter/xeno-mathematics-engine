package proofengine.s2.api_break

# Policy for API breaking changes requiring semver and changelog
import rego.v1

# Deny if API version change without semver bump
deny contains msg if {
    input.api_version_changed == true
    not input.semver_bump
    msg := "API version changed without semantic versioning bump"
}

# Deny if breaking change without changelog
deny contains msg if {
    input.breaking_changes == true
    not input.changelog_updated
    msg := "Breaking changes require changelog update"
}

# Deny if missing API tests for compatibility
deny contains msg if {
    input.api_tests_missing == true
    msg := "API compatibility tests required for version changes"
}

# Allow if all requirements met
allow if {
    input.semver_bump == true
    input.changelog_updated == true
    input.api_tests_present == true
}

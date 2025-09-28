package proofengine.policy.semver

# Semantic versioning policy
import rego.v1

# Deny if version change without semver bump
deny contains msg if {
    input.version_changed == true
    not input.semver_bump
    msg := "Version changes require semantic versioning bump"
}

# Deny if breaking change without major version bump
deny contains msg if {
    input.breaking_changes == true
    input.version_bump_type != "major"
    msg := "Breaking changes require major version bump"
}

# Allow if semver requirements met
allow if {
    input.semver_bump == true
    not (input.breaking_changes == true and input.version_bump_type != "major")
}
package proofengine.policy.changelog

# Changelog policy
import rego.v1

# Deny if breaking change without changelog
deny contains msg if {
    input.breaking_changes == true
    not input.changelog_updated
    msg := "Breaking changes require changelog update"
}

# Deny if changelog missing required sections
deny contains msg if {
    input.changelog_updated == true
    not input.changelog_has_breaking_section
    input.breaking_changes == true
    msg := "Changelog must include breaking changes section"
}

# Allow if changelog requirements met
allow if {
    not input.breaking_changes == true or input.changelog_updated == true
}
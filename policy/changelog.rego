package proof.changelog

# Deny if API changes without changelog update
deny[msg] {
    input.api_change != "none"
    not input.changelog.updated
    msg := "changelog must be updated for API changes"
}

# Deny if breaking changes without proper changelog entry
deny[msg] {
    input.api_change == "breaking"
    input.changelog.updated
    not input.changelog.breaking_section
    msg := "breaking changes must be documented in changelog breaking section"
}

# Deny if new features without changelog entry
deny[msg] {
    input.api_change == "public_add"
    input.changelog.updated
    not input.changelog.features_section
    msg := "new features must be documented in changelog features section"
}

# Allow if no API changes
allow {
    input.api_change == "none"
}

# Allow if API changes with proper changelog
allow {
    input.api_change != "none"
    input.changelog.updated
    input.changelog.breaking_section
    input.changelog.features_section
}

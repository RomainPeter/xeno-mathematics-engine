package proof.semver

# Deny if public API addition without minor version bump
deny[msg] {
    input.api_change == "public_add"
    not input.version.bumped_minor
    msg := "public API addition requires minor version bump"
}

# Deny if breaking change without major version bump
deny[msg] {
    input.api_change == "breaking"
    not input.version.bumped_major
    msg := "breaking API change requires major version bump"
}

# Deny if patch change with API modifications
deny[msg] {
    input.api_change != "none"
    input.version.bumped_patch
    not input.version.bumped_minor
    msg := "API changes require at least minor version bump"
}

# Allow patch bumps only for bug fixes
allow {
    input.api_change == "none"
    input.version.bumped_patch
}

# Allow minor bumps for new features
allow {
    input.api_change == "public_add"
    input.version.bumped_minor
    not input.version.bumped_major
}

# Allow major bumps for breaking changes
allow {
    input.api_change == "breaking"
    input.version.bumped_major
}

package policy

# Policy: Retain sensitive data only with legal basis
# Domain: RegTech/Code
# Version: v0.1

deny[msg] {
    input.data_class == "sensitive"
    not input.has_legal_basis
    msg := "Missing legal basis for sensitive data"
}

deny[msg] {
    input.data_class == "sensitive"
    input.has_legal_basis
    not input.legal_basis_valid
    msg := "Invalid legal basis for sensitive data"
}

deny[msg] {
    input.data_class == "sensitive"
    input.has_legal_basis
    input.legal_basis_valid
    input.retention_period > input.max_retention_period
    msg := "Retention period exceeds maximum allowed"
}

# Allow sensitive data if all conditions are met
allow {
    input.data_class == "sensitive"
    input.has_legal_basis
    input.legal_basis_valid
    input.retention_period <= input.max_retention_period
}

# Allow non-sensitive data
allow {
    input.data_class != "sensitive"
}
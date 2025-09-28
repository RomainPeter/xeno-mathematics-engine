package policy

# Data minimization policy
# Deny access to personal data without proper consent and clear purpose

deny[msg] {
    input.data_category == "personal"
    not input.has_consent
    msg := "Missing consent for personal data access"
}

deny[msg] {
    input.data_category == "personal"
    input.purpose_unclear
    msg := "Purpose for personal data collection is unclear"
}

deny[msg] {
    input.data_category == "personal"
    input.data_retention_period > 365
    msg := "Personal data retention period exceeds 1 year limit"
}

# Allow access if all conditions are met
allow {
    input.data_category == "personal"
    input.has_consent
    not input.purpose_unclear
    input.data_retention_period <= 365
}
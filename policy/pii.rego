package pii

# PII detection and redaction policy (PR F scope)
# Ensures PII is not logged or exposed with high precision, low noise

import rego.v1

# PII patterns (high precision, low false positives)
# Email: RFC compliant, excludes test fixtures
email_detected {
    input.files[_].content =~ "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    not input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
}

# Phone E.164 format
phone_e164_detected {
    input.files[_].content =~ "\\+?[1-9]\\d{7,14}"
    not input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
}

# US SSN (strict pattern, exclude test fixtures)
ssn_detected {
    input.files[_].content =~ "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    not input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
    not input.files[_].content =~ "123-45-6789|000-00-0000"  # Common test values
}

# French NIR (disabled by default, flag-controlled)
nir_fr_detected {
    input.policy_flags.pii.fr_nir == true
    input.files[_].content =~ "\\b\\d{13}\\b"
    not input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
}

# Quasi-PII secrets (AWS, Google, Stripe keys)
secret_keys_detected {
    input.files[_].content =~ "(AKIA|SECRET|pk_live_|sk_live_|AIza)"
    not input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
}

# PII in logs (redaction required)
pii_logging {
    input.logs[_].content =~ "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    not input.logs[_].redacted
}

# Require PII redaction in logs
require_pii_redaction {
    input.logs[_].content =~ "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    not input.pii_redaction_enabled
}

# Scan scope validation
scan_scope_violation {
    input.files[_].path =~ ".*/(test|fixture|example|demo)/.*"
    input.files[_].content =~ "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    input.policy_flags.pii.scan_diff_only == true
}

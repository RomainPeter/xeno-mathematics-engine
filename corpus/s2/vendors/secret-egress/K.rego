package proofengine.s2.secret_egress

# Policy for secret and egress prevention
import rego.v1

# Deny if secrets detected in code
deny contains msg if {
    input.secrets_detected == true
    msg := "Secrets detected in codebase"
}

# Deny if unauthorized egress attempted
deny contains msg if {
    input.egress_attempted == true
    input.egress_authorized == false
    msg := "Unauthorized network egress detected"
}

# Deny if API keys in plaintext
deny contains msg if {
    input.api_keys_plaintext == true
    msg := "API keys must not be stored in plaintext"
}

# Allow if all security requirements met
allow if {
    input.secrets_detected == false
    input.egress_attempted == false
    input.api_keys_encrypted == true
    input.guard_checks_passed == true
}

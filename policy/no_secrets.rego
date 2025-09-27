package proofengine.policy.no_secrets

# No secrets policy
import rego.v1

# Deny if secrets detected
deny contains msg if {
    input.secrets_detected == true
    msg := "Secrets detected in codebase"
}

# Deny if API keys in plaintext
deny contains msg if {
    input.api_keys_plaintext == true
    msg := "API keys must not be stored in plaintext"
}

# Deny if secrets in environment variables
deny contains msg if {
    input.secrets_in_env == true
    msg := "Secrets must not be stored in environment variables"
}

# Allow if no secrets detected
allow if {
    input.secrets_detected == false
    input.api_keys_plaintext == false
    input.secrets_in_env == false
}
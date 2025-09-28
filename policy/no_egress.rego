package proofengine.policy.no_egress

# No egress policy
import rego.v1

# Deny if unauthorized egress
deny contains msg if {
    input.egress_attempted == true
    input.egress_authorized == false
    msg := "Unauthorized network egress detected"
}

# Deny if external API calls without authorization
deny contains msg if {
    input.external_api_calls == true
    input.api_calls_authorized == false
    msg := "External API calls must be authorized"
}

# Allow if egress requirements met
allow if {
    input.egress_attempted == false or input.egress_authorized == true
}

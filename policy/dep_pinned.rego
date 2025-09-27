package proofengine.policy.dep_pinned

# Dependency pinning policy
import rego.v1

# Deny if dependencies not pinned
deny contains msg if {
    input.dependency_unpinned == true
    msg := "Dependencies must be pinned to specific versions"
}

# Deny if CVE detected
deny contains msg if {
    input.cve_detected == true
    input.cve_severity in ["HIGH", "CRITICAL"]
    msg := sprintf("Critical vulnerability: %s", [input.cve_id])
}

# Deny if typosquatting detected
deny contains msg if {
    input.typosquat_detected == true
    msg := sprintf("Typosquatting detected: %s", [input.package_name])
}

# Allow if security requirements met
allow if {
    input.dependency_pinned == true
    input.cve_detected == false
    input.typosquat_detected == false
}

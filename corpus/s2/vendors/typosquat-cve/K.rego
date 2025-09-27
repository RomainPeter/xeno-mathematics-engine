package proofengine.s2.typosquat_cve

# Policy for dependency security
import rego.v1

# Deny if dependency not pinned to specific version
deny contains msg if {
    input.dependency_unpinned == true
    msg := "Dependencies must be pinned to specific versions"
}

# Deny if CVE detected in dependencies
deny contains msg if {
    input.cve_detected == true
    input.cve_severity in ["HIGH", "CRITICAL"]
    msg := sprintf("Critical vulnerability detected: %s", [input.cve_id])
}

# Deny if typosquatting detected
deny contains msg if {
    input.typosquat_detected == true
    msg := sprintf("Typosquatting detected in package: %s", [input.package_name])
}

# Allow if all security requirements met
allow if {
    input.dependency_pinned == true
    input.cve_detected == false
    input.typosquat_detected == false
    input.sbom_updated == true
}

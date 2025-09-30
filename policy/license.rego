package license

# License compliance policy (PR F allowlist/denylist)
# Ensures proper license handling with allowlist approach

import rego.v1

# Allowlist (permissive licenses)
allowlist_licenses := [
    "MIT",
    "Apache-2.0", 
    "BSD-2-Clause",
    "BSD-3-Clause",
    "MPL-2.0",
    "ISC",
    "GPL-2.0-with-classpath-exception"
]

# Denylist (incompatible licenses)
denylist_licenses := [
    "AGPL-3.0",
    "AGPL-3.0-only", 
    "AGPL-3.0-or-later",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "SSPL-1.0"
]

# Check for denylist license violations
license_violation_denylist {
    input.dependencies[_].license == denylist_licenses[_]
    not input.license_exceptions[_].package == input.dependencies[_].name
}

# Check for AGPL specifically (expected-fail case)
license_violation_agpl {
    input.dependencies[_].license =~ "AGPL.*"
    not input.license_exceptions[_].package == input.dependencies[_].name
}

# Check for missing license information
missing_license {
    not input.license_file
    not input.package_json.license
    not input.sbom.license_info
}

# Check for UNKNOWN/NOASSERTION licenses (warning only)
unknown_license_warning {
    input.dependencies[_].license =~ "(UNKNOWN|NOASSERTION)"
    input.policy_flags.license.unknown == "warn"
}

# Dual licensing check (allow if one license is allowlist)
dual_license_violation {
    input.dependencies[_].dual_license
    not input.dependencies[_].license_primary in allowlist_licenses
    not input.dependencies[_].license_secondary in allowlist_licenses
}

# Require license allowlist configuration
require_license_allowlist {
    input.dependencies[_]
    not input.license_allowlist_configured
}

# Check for license file in repository
license_file_required {
    not input.files[_].path =~ "LICENSE|license"
}

# Exception file validation
license_exception_required {
    input.dependencies[_].license in denylist_licenses
    not input.license_exceptions[_].package == input.dependencies[_].name
    not input.license_exception_file
}

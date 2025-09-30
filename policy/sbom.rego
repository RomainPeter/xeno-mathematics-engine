package sbom

# SBOM (Software Bill of Materials) policy
# Ensures SBOM integrity and completeness

import rego.v1

# Check for SBOM tampering
sbom_tamper {
    input.sbom_hash != input.expected_sbom_hash
}

# Check for missing SBOM
missing_sbom {
    not input.sbom_file
}

# Check for incomplete SBOM
incomplete_sbom {
    input.sbom.components[_]
    not input.sbom.components[_].purl
}

# Check for SBOM consistency with dependencies
sbom_consistency {
    input.dependencies[_]
    not input.sbom.components[_].name == input.dependencies[_].name
}

# Require SBOM for all dependencies
require_sbom_for_deps {
    input.dependencies[_]
    not input.sbom.components[_].name == input.dependencies[_].name
}

package provenance

# Software provenance policy
# Ensures build provenance and supply chain integrity

import rego.v1

# Check for provenance mismatch
provenance_mismatch {
    input.provenance.builder_id != input.expected_builder_id
}

# Check for missing provenance
missing_provenance {
    not input.provenance_file
}

# Check for invalid provenance signature
invalid_provenance_signature {
    input.provenance.signature
    not input.provenance.signature_valid
}

# Check for provenance timestamp
provenance_timestamp {
    input.provenance.timestamp
    input.provenance.timestamp > input.build_timestamp
}

# Require provenance for all artifacts
require_provenance {
    input.artifacts[_]
    not input.provenance.artifacts[_] == input.artifacts[_]
}

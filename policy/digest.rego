package digest

# Digest pinning policy
# Ensures all dependencies are pinned to specific digests

import rego.v1

# Check for unpinned dependencies
unpinned_dep {
    input.dependencies[_]
    not input.dependencies[_].digest
}

# Check for floating tags
floating_tag {
    input.dependencies[_].version =~ "latest|main|master"
}

# Check for digest format
invalid_digest_format {
    input.dependencies[_].digest
    not input.dependencies[_].digest =~ "sha256:[a-f0-9]{64}"
}

# Require digest for all dependencies
require_digest {
    input.dependencies[_]
    not input.dependencies[_].digest
}

# Check for digest consistency
digest_consistency {
    input.dependencies[_].digest
    input.dependencies[_].digest != input.lockfile.dependencies[_].digest
}

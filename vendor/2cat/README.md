# 2cat Vendor Package

This directory contains the 2cat vendor package for the xeno-mathematics-engine.

## Files

- `2cat.lock` - Lock file with package metadata and verification information
- `2cat-pack.tar.gz` - The actual vendor package (not included in repo)
- `2cat-pack.tar.gz.minisig` - Digital signature for the package (not included in repo)

## Verification

Use the verification script to check package integrity:

```bash
./scripts/verify_2cat_pack.sh
```

This script will:
1. Check that all required files exist
2. Verify SHA256 checksum matches the lock file
3. Verify the digital signature using minisign

## Security

The package is cryptographically signed and the checksum is locked in the lock file to ensure reproducible builds and prevent tampering.
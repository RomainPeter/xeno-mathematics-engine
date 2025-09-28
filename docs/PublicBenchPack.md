# Public Bench Pack

## Contents
- out/bench/summary.json
- seeds used + versions
- merkle.txt + signature
- sbom.json

## How to verify
```bash
cosign verify-blob merkle.sig -b merkle.txt
```
Check SBOM has 0 High/Critical

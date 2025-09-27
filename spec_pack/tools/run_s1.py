#!/usr/bin/env python3
import subprocess
import sys

cmd = [sys.executable, "spec_pack/tools/verify.py", "--s1"]
print("Running S1 audit checks (minimality, trace bound, provenance)...")
p = subprocess.run(cmd, capture_output=True, text=True)
print(p.stdout)
if p.returncode != 0:
    print(p.stderr, file=sys.stderr)
    sys.exit(1)
print("S1 suite (subset) PASS")

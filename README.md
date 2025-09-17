# Architect of Proof
Ambition→Hostility compiler and Logical Safe for regulated AI. We don’t promise — we compile ambition into obligations, invariants, and hostile tests, and we carry proofs.

[![Proof CI](https://github.com/romainpeter/architect-of-proof/actions/workflows/proof-ci.yml/badge.svg?branch=main)](https://github.com/romainpeter/architect-of-proof/actions/workflows/proof-ci.yml)
[![Proof Nightly](https://github.com/romainpeter/architect-of-proof/actions/workflows/proof-nightly.yml/badge.svg)](https://github.com/romainpeter/architect-of-proof/actions/workflows/proof-nightly.yml)

Quickstart
- make a2h      # compile Ambition → Hostility, emit report, journalize and merklize
- make s1       # benign audit suite
- make s2       # incident harness (contradiction → retro-rule, contested, S1 still PASS)

Local strict CI (hooks)
- ./install_hooks.sh --force
- pre-commit: A2H_check + S1; pre-push: A2H_check + S1+S2.

What’s inside
- spec_pack/: ANF, obligations/invariants, tests S1/S2, PCAP, journal, metrics, A2H compiler.
- .github/workflows/: Proof CI.

License
Apache-2.0

package repro

# Reproducibility policy
# Ensures reproducible builds and tests

import rego.v1

# Check for missing random seeds
missing_seed {
    input.tests[_].random_operations
    not input.tests[_].seed
}

# Check for non-deterministic ordering
nondet_ordering {
    input.tests[_].ordering = "random"
    not input.tests[_].seed
}

# Check for flaky tests
flaky_test {
    input.tests[_].reruns > 1
    not input.tests[_].deterministic
}

# Require reproducible tests
require_repro_rule {
    input.tests[_]
    not input.tests[_].reproducible
}

# Check for performance budget violations
perf_budget_violation {
    input.tests[_].p95_latency > input.performance_budget.p95_threshold
}

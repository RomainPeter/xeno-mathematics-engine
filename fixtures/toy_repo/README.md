# Toy Repository for Code Compliance Testing

This repository contains intentional code compliance violations and compliant examples for testing CEGIS convergence.

## Files

- `violations.py` - Contains intentional violations of code compliance rules
- `compliant.py` - Contains compliant code as reference
- `README.md` - This file

## Violation Types

### 1. Deprecated API Usage
- `foo_v1()`, `bar_v1()`, `baz_v1()` - Deprecated API calls
- `old_function()`, `legacy_method()` - Legacy function names
- `deprecated_api_call()` - Deprecated API usage

### 2. Naming Convention Violations
- `PascalCaseFunction()` - Should be `snake_case_function()`
- `camelCaseClass` - Should be `PascalCaseClass`
- `camelCaseVariable` - Should be `snake_case_variable`

### 3. Security Vulnerabilities
- `eval()` usage - Should use `ast.literal_eval()`
- `os.system()` usage - Should use `subprocess.run()`
- `random.random()` for passwords - Should use `secrets.token_hex()`

### 4. Code Style Issues
- Lines longer than 120 characters
- Trailing whitespace
- Inconsistent formatting

## Expected CEGIS Convergence

The CEGIS algorithm should converge on fixes for these violations within 5 iterations:

1. **Iteration 1**: Detect violations
2. **Iteration 2**: Propose initial fixes
3. **Iteration 3**: Refine based on counterexamples
4. **Iteration 4**: Further refinement
5. **Iteration 5**: Convergence to compliant code

## Test Scenarios

### Scenario 1: Deprecated API Fix
- **Input**: `foo_v1("input")`
- **Expected**: `foo_v2("input")`
- **Convergence**: Should converge in 2-3 iterations

### Scenario 2: Naming Convention Fix
- **Input**: `PascalCaseFunction()`
- **Expected**: `snake_case_function()`
- **Convergence**: Should converge in 2-3 iterations

### Scenario 3: Security Fix
- **Input**: `eval(user_input)`
- **Expected**: `ast.literal_eval(user_input)`
- **Convergence**: Should converge in 2-3 iterations

### Scenario 4: Mixed Violations
- **Input**: Multiple violations in one function
- **Expected**: All violations fixed
- **Convergence**: Should converge in 3-5 iterations

## Usage

```python
from fixtures.toy_repo.violations import old_function, PascalCaseFunction
from fixtures.toy_repo.compliant import new_function, snake_case_function

# Test violations
violations = old_function()  # Contains deprecated APIs

# Test compliant code
compliant = new_function()  # Uses modern APIs
```

## CEGIS Testing

This repository is designed to test CEGIS convergence with:

1. **Deterministic mode**: All fixes should be predictable
2. **Hybrid mode**: LLM-based fixes with fallback
3. **Convergence testing**: Should converge within 5 iterations
4. **PCAP emission**: Each iteration should emit PCAP
5. **Event tracking**: All events should be tracked

## Expected Results

- **Convergence**: < 5 iterations for all scenarios
- **Success rate**: 100% for deterministic mode
- **Performance**: < 100ms per iteration
- **PCAP emission**: One PCAP per iteration
- **Event correlation**: All events properly correlated

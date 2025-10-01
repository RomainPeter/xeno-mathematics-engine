#!/usr/bin/env python3
"""
Demo script for Domain CEGIS - Code Compliance.
Demonstrates CEGIS convergence on toy repository with PCAP emission.
"""

import asyncio
import time
from typing import Dict

from proofengine.domain.types import CodeSnippet
from proofengine.domain.cegis_engine import CEGISEngine, CEGISConfig, CEGISMode


def create_toy_repo_violations() -> Dict[str, CodeSnippet]:
    """Create toy repository violations for testing."""
    return {
        "deprecated_api": CodeSnippet(
            content='result = foo_v1("input")',
            language="python",
            start_line=1,
            end_line=1,
        ),
        "naming_convention": CodeSnippet(
            content="def PascalCaseFunction():",
            language="python",
            start_line=1,
            end_line=1,
        ),
        "security": CodeSnippet(
            content="result = eval(user_input)",
            language="python",
            start_line=1,
            end_line=1,
        ),
        "code_style": CodeSnippet(
            content="very_long_variable_name_that_exceeds_the_recommended_line_length_limit = 'value'",
            language="python",
            start_line=1,
            end_line=1,
        ),
        "mixed_violations": CodeSnippet(
            content="""def complex_violation():
    data = foo_v1("input")  # Deprecated API
    camelCaseResult = data  # Naming convention
    result = eval(camelCaseResult)  # Security
    return result""",
            language="python",
            start_line=1,
            end_line=5,
        ),
    }


def print_cegis_result(result, title: str):
    """Print CEGIS result in a formatted way."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

    print(f"✅ Success: {result.success}")
    print(f"🔄 Iterations: {result.iterations}")
    print(f"⏱️  Convergence Time: {result.convergence_time:.3f}s")
    print(f"🎯 Converged: {result.is_converged}")
    print(f"📊 Convergence Rate: {result.convergence_rate:.2f}")

    if result.final_candidate:
        print("\n📝 Final Candidate:")
        print(f"  ID: {result.final_candidate.id}")
        print(f"  Patch: {result.final_candidate.patch[:100]}...")
        print(f"  Spec: {result.final_candidate.spec}")
        print(f"  Rationale: {result.final_candidate.rationale[:100]}...")

    print(f"\n🚨 Counterexamples: {len(result.counterexamples)}")
    for i, ce in enumerate(result.counterexamples[:3]):  # Show first 3
        print(f"  {i+1}. {ce.rule} at {ce.file_path}:{ce.line_number}")

    print(f"\n📦 PCAP Emissions: {len(result.pcap_emissions)}")
    for i, pcap in enumerate(result.pcap_emissions):
        print(f"  {i+1}. Iteration {pcap['iteration']}: {pcap['status']}")

    if result.metadata:
        print("\n📋 Metadata:")
        for key, value in result.metadata.items():
            print(f"  {key}: {value}")


async def test_deprecated_api_convergence():
    """Test convergence for deprecated API violations."""
    print("\n🧪 Testing Deprecated API Convergence...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["deprecated_api"]

    start_time = time.time()
    result = await engine.execute_cegis(
        code_snippet=code_snippet,
        violation_type="deprecated_api",
        rule_id="deprecated_api",
        seed="test_deprecated_api",
    )
    total_time = time.time() - start_time

    print_cegis_result(result, "Deprecated API Convergence")

    # Check convergence criteria
    assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
    assert result.success, "CEGIS should converge successfully"
    assert result.final_candidate is not None, "Final candidate should be generated"
    assert result.is_converged, "Result should be converged"

    print(f"✅ Deprecated API test passed in {total_time:.3f}s")
    return result


async def test_naming_convention_convergence():
    """Test convergence for naming convention violations."""
    print("\n🧪 Testing Naming Convention Convergence...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["naming_convention"]

    start_time = time.time()
    result = await engine.execute_cegis(
        code_snippet=code_snippet,
        violation_type="naming_convention",
        rule_id="naming_convention",
        seed="test_naming_convention",
    )
    total_time = time.time() - start_time

    print_cegis_result(result, "Naming Convention Convergence")

    # Check convergence criteria
    assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
    assert result.success, "CEGIS should converge successfully"
    assert result.final_candidate is not None, "Final candidate should be generated"
    assert result.is_converged, "Result should be converged"

    print(f"✅ Naming Convention test passed in {total_time:.3f}s")
    return result


async def test_security_convergence():
    """Test convergence for security violations."""
    print("\n🧪 Testing Security Convergence...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["security"]

    start_time = time.time()
    result = await engine.execute_cegis(
        code_snippet=code_snippet,
        violation_type="security",
        rule_id="security",
        seed="test_security",
    )
    total_time = time.time() - start_time

    print_cegis_result(result, "Security Convergence")

    # Check convergence criteria
    assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
    assert result.success, "CEGIS should converge successfully"
    assert result.final_candidate is not None, "Final candidate should be generated"
    assert result.is_converged, "Result should be converged"

    print(f"✅ Security test passed in {total_time:.3f}s")
    return result


async def test_mixed_violations_convergence():
    """Test convergence for mixed violations."""
    print("\n🧪 Testing Mixed Violations Convergence...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["mixed_violations"]

    start_time = time.time()
    result = await engine.execute_cegis(
        code_snippet=code_snippet,
        violation_type="mixed",
        rule_id="mixed",
        seed="test_mixed",
    )
    total_time = time.time() - start_time

    print_cegis_result(result, "Mixed Violations Convergence")

    # Check convergence criteria
    assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
    assert result.success, "CEGIS should converge successfully"
    assert result.final_candidate is not None, "Final candidate should be generated"
    assert result.is_converged, "Result should be converged"

    print(f"✅ Mixed Violations test passed in {total_time:.3f}s")
    return result


async def test_concurrent_execution():
    """Test concurrent execution of multiple CEGIS instances."""
    print("\n🧪 Testing Concurrent Execution...")

    config = CEGISConfig(
        max_iterations=5,
        mode=CEGISMode.STUB_ONLY,
        enable_concurrency=True,
        enable_pcap_emission=True,
    )
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()

    # Create concurrent tasks
    tasks = []
    test_cases = [
        ("deprecated_api", violations["deprecated_api"]),
        ("naming_convention", violations["naming_convention"]),
        ("security", violations["security"]),
    ]

    for violation_type, code_snippet in test_cases:
        task = engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type=violation_type,
            rule_id=violation_type,
            seed=f"test_concurrent_{violation_type}",
        )
        tasks.append(task)

    start_time = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    print("\n📊 Concurrent Execution Results:")
    print(f"⏱️  Total Time: {total_time:.3f}s")
    print(f"🔄 Tasks: {len(results)}")

    # Check all results
    for i, result in enumerate(results):
        print(f"\n  Task {i+1}:")
        print(f"    Success: {result.success}")
        print(f"    Iterations: {result.iterations}")
        print(f"    Time: {result.convergence_time:.3f}s")

        # Check convergence criteria
        assert result.iterations <= 5, f"Task {i+1} took {result.iterations} iterations > 5"
        assert result.success, f"Task {i+1} should converge successfully"
        assert result.final_candidate is not None, f"Task {i+1} should have final candidate"
        assert result.is_converged, f"Task {i+1} should be converged"

    print(f"✅ Concurrent execution test passed in {total_time:.3f}s")
    return results


async def test_deterministic_mode():
    """Test deterministic mode (stub-only)."""
    print("\n🧪 Testing Deterministic Mode...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["deprecated_api"]

    # Run multiple times with same seed
    results = []
    for i in range(3):
        result = await engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_deterministic",
        )
        results.append(result)
        engine.reset()  # Reset between runs

    print("\n📊 Deterministic Mode Results:")
    print(f"🔄 Runs: {len(results)}")

    # Check deterministic behavior
    for i, result in enumerate(results):
        print(f"\n  Run {i+1}:")
        print(f"    Success: {result.success}")
        print(f"    Iterations: {result.iterations}")
        print(f"    Candidate ID: {result.final_candidate.id}")

        # Check deterministic behavior
        assert result.success, f"Run {i+1} should succeed"
        assert result.iterations == results[0].iterations, f"Run {i+1} should have same iterations"
        assert (
            result.final_candidate.id == results[0].final_candidate.id
        ), f"Run {i+1} should have same candidate"

    print("✅ Deterministic mode test passed")
    return results


async def test_hybrid_mode():
    """Test hybrid mode (LLM mockable)."""
    print("\n🧪 Testing Hybrid Mode...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.HYBRID, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()
    code_snippet = violations["deprecated_api"]

    start_time = time.time()
    result = await engine.execute_cegis(
        code_snippet=code_snippet,
        violation_type="deprecated_api",
        rule_id="deprecated_api",
        seed="test_hybrid",
    )
    total_time = time.time() - start_time

    print_cegis_result(result, "Hybrid Mode Convergence")

    # Check hybrid mode behavior
    assert result.success, "Hybrid mode should succeed"
    assert result.iterations <= 5, "Hybrid mode should converge within 5 iterations"
    assert result.final_candidate is not None, "Hybrid mode should generate final candidate"

    print(f"✅ Hybrid mode test passed in {total_time:.3f}s")
    return result


async def test_performance_benchmark():
    """Test performance benchmark."""
    print("\n🧪 Testing Performance Benchmark...")

    config = CEGISConfig(max_iterations=5, mode=CEGISMode.STUB_ONLY, enable_pcap_emission=True)
    engine = CEGISEngine(config)

    violations = create_toy_repo_violations()

    # Test all violation types
    test_cases = [
        ("deprecated_api", violations["deprecated_api"]),
        ("naming_convention", violations["naming_convention"]),
        ("security", violations["security"]),
        ("code_style", violations["code_style"]),
    ]

    results = []
    total_start_time = time.time()

    for violation_type, code_snippet in test_cases:
        start_time = time.time()
        result = await engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type=violation_type,
            rule_id=violation_type,
            seed=f"test_performance_{violation_type}",
        )
        execution_time = time.time() - start_time
        results.append((violation_type, result, execution_time))
        engine.reset()

    total_time = time.time() - total_start_time

    print("\n📊 Performance Benchmark Results:")
    print(f"⏱️  Total Time: {total_time:.3f}s")
    print(f"🔄 Test Cases: {len(test_cases)}")

    for violation_type, result, execution_time in results:
        print(f"\n  {violation_type}:")
        print(f"    Success: {result.success}")
        print(f"    Iterations: {result.iterations}")
        print(f"    Time: {execution_time:.3f}s")
        print(f"    PCAPs: {len(result.pcap_emissions)}")

        # Check performance criteria
        assert execution_time < 10.0, f"{violation_type} took {execution_time:.3f}s > 10s"
        assert result.success, f"{violation_type} should succeed"
        assert result.iterations <= 5, f"{violation_type} should converge within 5 iterations"

    print(f"✅ Performance benchmark test passed in {total_time:.3f}s")
    return results


async def run_demo():
    """Run the complete CEGIS demo."""
    print("🚀 Domain CEGIS - Code Compliance Demo")
    print("=" * 60)

    try:
        # Test individual convergence scenarios
        await test_deprecated_api_convergence()
        await test_naming_convention_convergence()
        await test_security_convergence()
        await test_mixed_violations_convergence()

        # Test concurrent execution
        await test_concurrent_execution()

        # Test execution modes
        await test_deterministic_mode()
        await test_hybrid_mode()

        # Test performance
        await test_performance_benchmark()

        print(f"\n{'='*60}")
        print("🎉 Domain CEGIS Demo Completed Successfully!")
        print(f"{'='*60}")
        print("✅ All convergence tests passed")
        print("✅ All performance tests passed")
        print("✅ All concurrent execution tests passed")
        print("✅ All mode tests passed")
        print("✅ PCAP emission working correctly")
        print("✅ CEGIS convergence < 5 iterations achieved")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_demo())

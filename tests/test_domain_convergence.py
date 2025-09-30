"""
Tests for domain convergence with CEGIS.
Tests convergence < N=5 iterations on toy repository.
"""

import pytest
import asyncio
import time

from proofengine.domain.types import CodeSnippet
from proofengine.domain.cegis_engine import CEGISEngine, CEGISConfig, CEGISMode


class TestConvergence:
    """Test CEGIS convergence on toy repository."""

    @pytest.fixture
    def cegis_config(self):
        """Create CEGIS configuration."""
        return CEGISConfig(
            max_iterations=5,
            timeout_per_iteration=30.0,
            mode=CEGISMode.STUB_ONLY,
            enable_concurrency=True,
            enable_pcap_emission=True,
            convergence_threshold=0.95,
        )

    @pytest.fixture
    def cegis_engine(self, cegis_config):
        """Create CEGIS engine."""
        return CEGISEngine(cegis_config)

    @pytest.fixture
    def toy_repo_violations(self):
        """Get toy repository violations."""
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
        }

    @pytest.mark.asyncio
    async def test_deprecated_api_convergence(self, cegis_engine, toy_repo_violations):
        """Test convergence for deprecated API violations."""
        code_snippet = toy_repo_violations["deprecated_api"]

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_deprecated_api",
        )

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"
        assert result.final_candidate is not None, "Final candidate should be generated"
        assert result.is_converged, "Result should be converged"

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"
        assert result.pcap_emissions[-1]["status"] == "converged", "Final PCAP should be converged"

    @pytest.mark.asyncio
    async def test_naming_convention_convergence(self, cegis_engine, toy_repo_violations):
        """Test convergence for naming convention violations."""
        code_snippet = toy_repo_violations["naming_convention"]

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="naming_convention",
            rule_id="naming_convention",
            seed="test_naming_convention",
        )

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"
        assert result.final_candidate is not None, "Final candidate should be generated"
        assert result.is_converged, "Result should be converged"

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"
        assert result.pcap_emissions[-1]["status"] == "converged", "Final PCAP should be converged"

    @pytest.mark.asyncio
    async def test_security_convergence(self, cegis_engine, toy_repo_violations):
        """Test convergence for security violations."""
        code_snippet = toy_repo_violations["security"]

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="security",
            rule_id="security",
            seed="test_security",
        )

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"
        assert result.final_candidate is not None, "Final candidate should be generated"
        assert result.is_converged, "Result should be converged"

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"
        assert result.pcap_emissions[-1]["status"] == "converged", "Final PCAP should be converged"

    @pytest.mark.asyncio
    async def test_code_style_convergence(self, cegis_engine, toy_repo_violations):
        """Test convergence for code style violations."""
        code_snippet = toy_repo_violations["code_style"]

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="code_style",
            rule_id="code_style",
            seed="test_code_style",
        )

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"
        assert result.final_candidate is not None, "Final candidate should be generated"
        assert result.is_converged, "Result should be converged"

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"
        assert result.pcap_emissions[-1]["status"] == "converged", "Final PCAP should be converged"

    @pytest.mark.asyncio
    async def test_mixed_violations_convergence(self, cegis_engine):
        """Test convergence for mixed violations."""
        code_snippet = CodeSnippet(
            content="""def complex_violation():
    data = foo_v1("input")  # Deprecated API
    camelCaseResult = data  # Naming convention
    result = eval(camelCaseResult)  # Security
    return result""",
            language="python",
            start_line=1,
            end_line=5,
        )

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="mixed",
            rule_id="mixed",
            seed="test_mixed",
        )

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"
        assert result.final_candidate is not None, "Final candidate should be generated"
        assert result.is_converged, "Result should be converged"

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"
        assert result.pcap_emissions[-1]["status"] == "converged", "Final PCAP should be converged"

    @pytest.mark.asyncio
    async def test_convergence_performance(self, cegis_engine, toy_repo_violations):
        """Test convergence performance."""
        code_snippet = toy_repo_violations["deprecated_api"]

        start_time = time.time()
        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_performance",
        )
        total_time = time.time() - start_time

        # Check performance
        assert total_time < 10.0, f"Convergence took {total_time:.2f}s > 10s"
        assert (
            result.convergence_time < 10.0
        ), f"Convergence time {result.convergence_time:.2f}s > 10s"

        # Check convergence
        assert result.iterations <= 5, f"Convergence took {result.iterations} iterations > 5"
        assert result.success, "CEGIS should converge successfully"

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self, cegis_engine):
        """Test behavior when max iterations reached."""
        # Create a difficult case that might not converge
        code_snippet = CodeSnippet(
            content="impossible_violation = 'this_will_never_converge'",
            language="python",
            start_line=1,
            end_line=1,
        )

        # Use a config with fewer iterations
        config = CEGISConfig(max_iterations=2)
        engine = CEGISEngine(config)

        result = await engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="impossible",
            rule_id="impossible",
            seed="test_max_iterations",
        )

        # Check that max iterations was reached
        assert result.iterations == 2, f"Should reach max iterations, got {result.iterations}"
        assert not result.success, "Should not converge within max iterations"
        assert result.metadata["convergence_reason"] == "max_iterations_reached"

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, cegis_engine, toy_repo_violations):
        """Test concurrent execution."""
        code_snippet = toy_repo_violations["deprecated_api"]

        # Test concurrent execution
        tasks = []
        for i in range(3):
            task = cegis_engine.execute_cegis(
                code_snippet=code_snippet,
                violation_type="deprecated_api",
                rule_id="deprecated_api",
                seed=f"test_concurrent_{i}",
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Check all results
        for i, result in enumerate(results):
            assert result.iterations <= 5, f"Task {i} took {result.iterations} iterations > 5"
            assert result.success, f"Task {i} should converge successfully"
            assert result.final_candidate is not None, f"Task {i} should have final candidate"
            assert result.is_converged, f"Task {i} should be converged"

    @pytest.mark.asyncio
    async def test_pcap_emission(self, cegis_engine, toy_repo_violations):
        """Test PCAP emission during convergence."""
        code_snippet = toy_repo_violations["deprecated_api"]

        result = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_pcap",
        )

        # Check PCAP emissions
        assert len(result.pcap_emissions) > 0, "PCAP should be emitted"

        # Check PCAP structure
        for pcap in result.pcap_emissions:
            assert "iteration" in pcap, "PCAP should have iteration"
            assert "candidate_id" in pcap, "PCAP should have candidate_id"
            assert "status" in pcap, "PCAP should have status"
            assert "timestamp" in pcap, "PCAP should have timestamp"
            assert "metadata" in pcap, "PCAP should have metadata"

        # Check final PCAP
        final_pcap = result.pcap_emissions[-1]
        assert final_pcap["status"] == "converged", "Final PCAP should be converged"
        assert (
            final_pcap["iteration"] == result.iterations - 1
        ), "Final PCAP should have correct iteration"

    @pytest.mark.asyncio
    async def test_statistics_collection(self, cegis_engine, toy_repo_violations):
        """Test statistics collection during convergence."""
        code_snippet = toy_repo_violations["deprecated_api"]

        await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_statistics",
        )

        # Get statistics
        stats = cegis_engine.get_execution_statistics()

        # Check statistics
        assert "total_iterations" in stats, "Statistics should have total_iterations"
        assert "total_time" in stats, "Statistics should have total_time"
        assert "average_time" in stats, "Statistics should have average_time"
        assert "proposal_statistics" in stats, "Statistics should have proposal_statistics"
        assert "verification_statistics" in stats, "Statistics should have verification_statistics"
        assert "refinement_statistics" in stats, "Statistics should have refinement_statistics"

        # Check values
        assert stats["total_iterations"] > 0, "Should have executed iterations"
        assert stats["total_time"] > 0, "Should have execution time"
        assert stats["average_time"] > 0, "Should have average time"

    @pytest.mark.asyncio
    async def test_engine_reset(self, cegis_engine, toy_repo_violations):
        """Test engine reset functionality."""
        code_snippet = toy_repo_violations["deprecated_api"]

        # Execute first time
        result1 = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_reset_1",
        )

        # Check first execution
        assert result1.success, "First execution should succeed"
        assert len(result1.pcap_emissions) > 0, "First execution should emit PCAP"

        # Reset engine
        cegis_engine.reset()

        # Execute second time
        result2 = await cegis_engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_reset_2",
        )

        # Check second execution
        assert result2.success, "Second execution should succeed"
        assert len(result2.pcap_emissions) > 0, "Second execution should emit PCAP"

        # Check that engine was reset
        stats = cegis_engine.get_execution_statistics()
        assert stats["total_iterations"] == result2.iterations, "Statistics should be reset"

    @pytest.mark.asyncio
    async def test_deterministic_mode(self, toy_repo_violations):
        """Test deterministic mode (stub-only)."""
        config = CEGISConfig(mode=CEGISMode.STUB_ONLY)
        engine = CEGISEngine(config)

        code_snippet = toy_repo_violations["deprecated_api"]

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

        # Check deterministic behavior
        for i, result in enumerate(results):
            assert result.success, f"Result {i} should succeed"
            assert (
                result.iterations == results[0].iterations
            ), f"Result {i} should have same iterations"
            assert (
                result.final_candidate.id == results[0].final_candidate.id
            ), f"Result {i} should have same candidate"

    @pytest.mark.asyncio
    async def test_hybrid_mode(self, toy_repo_violations):
        """Test hybrid mode (LLM mockable)."""
        config = CEGISConfig(mode=CEGISMode.HYBRID)
        engine = CEGISEngine(config)

        code_snippet = toy_repo_violations["deprecated_api"]

        result = await engine.execute_cegis(
            code_snippet=code_snippet,
            violation_type="deprecated_api",
            rule_id="deprecated_api",
            seed="test_hybrid",
        )

        # Check hybrid mode behavior
        assert result.success, "Hybrid mode should succeed"
        assert result.iterations <= 5, "Hybrid mode should converge within 5 iterations"
        assert result.final_candidate is not None, "Hybrid mode should generate final candidate"

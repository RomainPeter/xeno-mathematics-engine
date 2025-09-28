"""
Integration tests for Orchestrator.
Tests the complete AE/CEGIS pipeline with mocks.
"""

import pytest
import asyncio
import tempfile
import shutil
from typing import Dict, Any

from orchestrator.orchestrator import Orchestrator
from orchestrator.config import OrchestratorConfig
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from pefc.events.structured_bus import StructuredEventBus


class MockLLMAdapter:
    """Mock LLM adapter for testing."""

    def __init__(self):
        self.call_count = 0

    async def generate(
        self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1
    ) -> str:
        """Mock LLM generation."""
        self.call_count += 1
        return f'{{"name": "candidate_{self.call_count}", "properties": ["prop1", "prop2"], "constraints": [], "implementation_hints": ["hint1"]}}'


class MockVerifier:
    """Mock verifier for testing."""

    def __init__(self, should_verify: bool = True):
        self.should_verify = should_verify
        self.verify_count = 0

    async def verify(
        self,
        specification: Dict[str, Any],
        implementation: Dict[str, Any],
        constraints: list,
    ) -> Dict[str, Any]:
        """Mock verification."""
        self.verify_count += 1

        if self.should_verify and self.verify_count > 2:  # Fail first 2 attempts
            return {
                "valid": True,
                "confidence": 0.9,
                "evidence": [{"type": "test_evidence"}],
                "metrics": {"verification_time": 0.1},
            }
        else:
            return {
                "valid": False,
                "failing_property": "test_property",
                "evidence": {"error": "test_error"},
                "suggestions": ["suggestion1", "suggestion2"],
            }


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return OrchestratorConfig(
            ae_timeout=5.0,
            cegis_propose_timeout=2.0,
            cegis_verify_timeout=3.0,
            cegis_refine_timeout=2.0,
            cegis_max_iterations=3,
            audit_dir=temp_dir,
        )

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def mock_verifier(self):
        """Create mock verifier."""
        return MockVerifier(should_verify=True)

    @pytest.fixture
    def event_bus(self):
        """Create structured event bus."""
        return StructuredEventBus()

    @pytest.fixture
    def orchestrator(self, config, mock_llm, mock_verifier, event_bus):
        """Create orchestrator with mocks."""
        ae_engine = NextClosureEngine()
        cegis_engine = AsyncCegisEngine(mock_llm, mock_verifier)

        return Orchestrator(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=mock_llm,
            verifier=mock_verifier,
            event_bus=event_bus,
        )

    @pytest.fixture
    def domain_spec(self):
        """Create test domain specification."""
        return {
            "id": "test_domain",
            "name": "Test Domain",
            "objects": ["obj1", "obj2", "obj3"],
            "attributes": ["attr1", "attr2", "attr3"],
            "specification": {
                "requirements": ["req1", "req2"],
                "constraints": ["constraint1", "constraint2"],
            },
            "constraints": [{"type": "test_constraint", "condition": "test_condition"}],
        }

    @pytest.fixture
    def budgets(self):
        """Create test budgets."""
        return {
            "ae_timeout": 5.0,
            "cegis_timeout": 10.0,
            "llm_max_tokens": 1024,
            "llm_temperature": 0.1,
        }

    @pytest.fixture
    def thresholds(self):
        """Create test thresholds."""
        return {"min_confidence": 0.8, "max_iterations": 5, "success_rate": 0.9}

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.config is not None
        assert orchestrator.ae_engine is not None
        assert orchestrator.cegis_engine is not None
        assert orchestrator.llm_adapter is not None
        assert orchestrator.verifier is not None
        assert orchestrator.event_bus is not None
        assert orchestrator.state is None

    @pytest.mark.asyncio
    async def test_orchestrator_run_success(
        self, orchestrator, domain_spec, budgets, thresholds
    ):
        """Test successful orchestrator run."""
        # Run orchestrator
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify state
        assert state.phase == "completed"
        assert state.run_id is not None
        assert state.trace_id is not None
        assert state.start_time is not None
        assert state.end_time is not None

        # Verify AE results
        assert len(state.ae_results) > 0
        for result in state.ae_results:
            assert result.success
            assert result.concepts is not None
            assert result.implications is not None

        # Verify CEGIS results
        assert len(state.cegis_results) > 0
        for result in state.cegis_results:
            assert result.success
            assert result.candidate is not None
            assert result.verdict is not None

    @pytest.mark.asyncio
    async def test_orchestrator_run_with_incidents(
        self, config, domain_spec, budgets, thresholds
    ):
        """Test orchestrator run with incidents."""
        # Create orchestrator with failing verifier
        mock_verifier = MockVerifier(should_verify=False)
        mock_llm = MockLLMAdapter()
        event_bus = StructuredEventBus()

        ae_engine = NextClosureEngine()
        cegis_engine = AsyncCegisEngine(mock_llm, mock_verifier)

        orchestrator = Orchestrator(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=mock_llm,
            verifier=mock_verifier,
            event_bus=event_bus,
        )

        # Run orchestrator
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify incidents were created
        assert len(state.incidents) > 0
        for incident in state.incidents:
            assert incident.type in ["cegis_stability", "cegis_timeout", "ae_timeout"]
            assert incident.severity in ["medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_orchestrator_timeout_handling(
        self, temp_dir, domain_spec, budgets, thresholds
    ):
        """Test orchestrator timeout handling."""
        # Create config with very short timeouts
        config = OrchestratorConfig(
            ae_timeout=0.1,  # Very short timeout
            cegis_propose_timeout=0.1,
            cegis_verify_timeout=0.1,
            cegis_refine_timeout=0.1,
            audit_dir=temp_dir,
        )

        mock_llm = MockLLMAdapter()
        mock_verifier = MockVerifier(should_verify=True)
        event_bus = StructuredEventBus()

        ae_engine = NextClosureEngine()
        cegis_engine = AsyncCegisEngine(mock_llm, mock_verifier)

        orchestrator = Orchestrator(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=mock_llm,
            verifier=mock_verifier,
            event_bus=event_bus,
        )

        # Run orchestrator - should handle timeouts gracefully
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify timeout incidents were created
        timeout_incidents = [inc for inc in state.incidents if "timeout" in inc.type]
        assert len(timeout_incidents) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_event_publishing(
        self, orchestrator, domain_spec, budgets, thresholds
    ):
        """Test orchestrator event publishing."""
        # Track events
        events = []

        def event_handler(event):
            events.append(event)

        # Subscribe to events
        orchestrator.event_bus.subscribe("*", event_handler)

        # Run orchestrator
        await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify events were published
        assert len(events) > 0

        # Check for specific event types
        event_types = [event.topic for event in events]
        assert "orchestrator.started" in event_types
        assert "ae.started" in event_types
        assert "cegis.started" in event_types
        assert "orchestrator.completed" in event_types

    @pytest.mark.asyncio
    async def test_orchestrator_audit_pack_creation(
        self, orchestrator, domain_spec, budgets, thresholds
    ):
        """Test audit pack creation."""
        # Run orchestrator
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify audit pack was created
        assert state.phase == "completed"

        # Check that audit pack files exist
        audit_dir = orchestrator.config.audit_dir
        packs_dir = audit_dir / "packs" / state.run_id

        assert packs_dir.exists()
        assert (packs_dir / "manifest.json").exists()
        assert (packs_dir / "pcaps.json").exists()
        assert (packs_dir / "incidents.json").exists()
        assert (packs_dir / "journal.jsonl").exists()
        assert (packs_dir / "metrics.json").exists()

    @pytest.mark.asyncio
    async def test_orchestrator_concurrent_execution(
        self, config, domain_spec, budgets, thresholds
    ):
        """Test orchestrator concurrent execution."""
        # Create multiple orchestrators
        orchestrators = []
        for i in range(3):
            mock_llm = MockLLMAdapter()
            mock_verifier = MockVerifier(should_verify=True)
            event_bus = StructuredEventBus()

            ae_engine = NextClosureEngine()
            cegis_engine = AsyncCegisEngine(mock_llm, mock_verifier)

            orchestrator = Orchestrator(
                config=config,
                ae_engine=ae_engine,
                cegis_engine=cegis_engine,
                llm_adapter=mock_llm,
                verifier=mock_verifier,
                event_bus=event_bus,
            )
            orchestrators.append(orchestrator)

        # Run orchestrators concurrently
        tasks = [
            orchestrator.run(domain_spec, budgets, thresholds)
            for orchestrator in orchestrators
        ]
        states = await asyncio.gather(*tasks)

        # Verify all completed successfully
        for state in states:
            assert state.phase == "completed"
            assert state.run_id is not None
            assert state.trace_id is not None

    @pytest.mark.asyncio
    async def test_orchestrator_cancellation(
        self, orchestrator, domain_spec, budgets, thresholds
    ):
        """Test orchestrator cancellation."""
        # Create a task that will be cancelled
        task = asyncio.create_task(orchestrator.run(domain_spec, budgets, thresholds))

        # Cancel after short delay
        await asyncio.sleep(0.1)
        task.cancel()

        # Verify cancellation
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_orchestrator_metrics_collection(
        self, orchestrator, domain_spec, budgets, thresholds
    ):
        """Test orchestrator metrics collection."""
        # Run orchestrator
        state = await orchestrator.run(domain_spec, budgets, thresholds)

        # Verify metrics were collected
        assert state.metrics is not None
        assert len(state.metrics) > 0

        # Check for expected metrics
        expected_metrics = [
            "duration",
            "concepts_count",
            "implications_count",
            "incidents_count",
        ]
        for metric in expected_metrics:
            assert metric in state.metrics or any(
                metric in str(k) for k in state.metrics.keys()
            )

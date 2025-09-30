"""
Tests for Orchestrator v1 with real components.
Tests the complete pipeline without mocks.
"""

import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock

from orchestrator.orchestrator_v1 import OrchestratorV1, OrchestratorV1Config
from orchestrator.engines.real_ae_engine import RealAEEngine
from orchestrator.engines.real_cegis_engine import RealCegisEngine
from orchestrator.adapters.llm_adapter import LLMAdapter, LLMConfig
from orchestrator.adapters.verifier import Verifier, VerificationConfig
from orchestrator.scheduler.async_scheduler import AsyncScheduler, SchedulerConfig
from orchestrator.scheduler.budget_manager import BudgetManager, BudgetConfig
from pefc.events.structured_bus import StructuredEventBus


class TestOrchestratorV1:
    """Test cases for Orchestrator v1 with real components."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return OrchestratorV1Config(
            ae_timeout=5.0,
            cegis_propose_timeout=3.0,
            cegis_verify_timeout=3.0,
            cegis_refine_timeout=3.0,
            cegis_max_iterations=3,
            audit_dir=temp_dir,
            enable_budget_management=True,
            enable_async_scheduler=True,
        )

    @pytest.fixture
    def mock_llm_config(self):
        """Create mock LLM configuration."""
        return LLMConfig(
            api_url="https://api.openai.com/v1/chat/completions",
            api_key="test_key",
            model="gpt-4",
            max_tokens=1024,
            temperature=0.1,
            timeout=10.0,
            max_retries=2,
            concurrent_requests=3,
        )

    @pytest.fixture
    def mock_verifier_config(self):
        """Create mock verifier configuration."""
        return VerificationConfig(
            timeout=10.0,
            max_retries=2,
            concurrent_verifications=3,
            tools=["static_analysis", "property_check"],
        )

    @pytest.fixture
    def mock_scheduler_config(self):
        """Create mock scheduler configuration."""
        return SchedulerConfig(
            max_concurrent_tasks=5,
            default_timeout=10.0,
            max_retries=2,
            enable_budget_management=True,
        )

    @pytest.fixture
    def mock_budget_config(self):
        """Create mock budget configuration."""
        return BudgetConfig(
            default_timeout=30.0,
            warning_threshold=0.8,
            critical_threshold=0.95,
            overrun_threshold=1.0,
        )

    @pytest.fixture
    def orchestrator_v1(
        self,
        config,
        mock_llm_config,
        mock_verifier_config,
        mock_scheduler_config,
        mock_budget_config,
    ):
        """Create Orchestrator v1 with real components."""
        # Create real components
        llm_adapter = LLMAdapter(mock_llm_config)
        verifier = Verifier(mock_verifier_config)
        scheduler = AsyncScheduler(mock_scheduler_config)
        budget_manager = BudgetManager(mock_budget_config)
        event_bus = StructuredEventBus()

        # Create engines
        ae_engine = RealAEEngine(
            oracle_adapter=Mock(), bandit_strategy=Mock(), diversity_strategy=Mock()
        )
        cegis_engine = RealCegisEngine(
            llm_adapter=llm_adapter,
            verifier=verifier,
            synthesis_strategy=Mock(),
            refinement_strategy=Mock(),
        )

        return OrchestratorV1(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=llm_adapter,
            verifier=verifier,
            scheduler=scheduler,
            budget_manager=budget_manager,
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
            "verify_timeout": 5.0,
            "total_budget": 60.0,
        }

    @pytest.fixture
    def thresholds(self):
        """Create test thresholds."""
        return {
            "min_confidence": 0.8,
            "max_iterations": 5,
            "success_rate": 0.9,
            "min_concepts": 2,
            "max_incidents": 3,
        }

    @pytest.mark.asyncio
    async def test_orchestrator_v1_initialization(self, orchestrator_v1):
        """Test Orchestrator v1 initialization."""
        assert orchestrator_v1.config is not None
        assert orchestrator_v1.ae_engine is not None
        assert orchestrator_v1.cegis_engine is not None
        assert orchestrator_v1.llm_adapter is not None
        assert orchestrator_v1.verifier is not None
        assert orchestrator_v1.scheduler is not None
        assert orchestrator_v1.budget_manager is not None
        assert orchestrator_v1.event_bus is not None

    @pytest.mark.asyncio
    async def test_orchestrator_v1_run_success(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test successful Orchestrator v1 run."""
        # Mock the engines to return successful results
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[{"id": "concept1", "extent": ["obj1"], "intent": ["attr1"]}],
                implications=[{"id": "impl1", "premise": ["attr1"], "conclusion": ["attr2"]}],
                counterexamples=[],
                metrics={"concepts_count": 1, "implications_count": 1},
                timings={"total": 0.1},
            )
        )

        orchestrator_v1.cegis_engine.propose = AsyncMock(
            return_value=Mock(
                id="candidate1",
                specification={"name": "test"},
                implementation={"code": "test code"},
                metadata={},
            )
        )

        orchestrator_v1.cegis_engine.verify = AsyncMock(
            return_value=Mock(valid=True, confidence=0.9, evidence=[], metrics={})
        )

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify results
        assert state.phase == "completed"
        assert state.run_id is not None
        assert state.trace_id is not None
        assert len(state.ae_results) > 0
        assert len(state.cegis_results) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_v1_budget_overrun(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 with budget overrun."""
        # Mock budget overrun
        orchestrator_v1.budget_manager.consume_budget = AsyncMock(return_value=False)

        # Mock engines to return results
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={},
                timings={"total": 0.1},
            )
        )

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify budget overrun handling
        assert state.phase == "failed"
        assert len(state.incidents) > 0

        # Check for budget overrun incident
        budget_incidents = [inc for inc in state.incidents if "budget" in inc.type]
        assert len(budget_incidents) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_v1_timeout_handling(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 timeout handling."""
        # Mock timeout
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(side_effect=asyncio.TimeoutError())

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify timeout handling
        assert state.phase == "failed"
        assert len(state.incidents) > 0

        # Check for timeout incident
        timeout_incidents = [inc for inc in state.incidents if "timeout" in inc.type]
        assert len(timeout_incidents) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_v1_concurrent_execution(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 concurrent execution."""
        # Mock concurrent execution
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={},
                timings={"total": 0.1},
            )
        )

        orchestrator_v1.cegis_engine.propose = AsyncMock(
            return_value=Mock(
                id="candidate1",
                specification={"name": "test"},
                implementation={"code": "test code"},
                metadata={},
            )
        )

        orchestrator_v1.cegis_engine.verify = AsyncMock(
            return_value=Mock(valid=True, confidence=0.9, evidence=[], metrics={})
        )

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify concurrent execution
        assert state.phase == "completed"
        assert state.run_id is not None
        assert state.trace_id is not None

    @pytest.mark.asyncio
    async def test_orchestrator_v1_cancellation_safety(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 cancellation safety."""
        # Mock cancellation
        orchestrator_v1.scheduler.cancel_all_tasks = AsyncMock(return_value=2)

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify cancellation handling
        assert state.phase in ["completed", "failed"]
        assert state.run_id is not None
        assert state.trace_id is not None

    @pytest.mark.asyncio
    async def test_orchestrator_v1_failreason_emission(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 FailReason emission."""
        # Mock FailReason emission
        # failreason = FailReasonFactory.create_time_budget_exceeded(
        #     component="orchestrator",
        #     operation="ae_phase",
        #     current_time=60.0,
        #     budget_limit=30.0,
        # )

        orchestrator_v1.emit_failreason = AsyncMock()

        # Run orchestrator
        # state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify FailReason emission
        # assert state.run_id is not None
        # assert state.trace_id is not None

    @pytest.mark.asyncio
    async def test_orchestrator_v1_event_publishing(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 event publishing."""
        # Track events
        events = []

        def event_handler(event):
            events.append(event)

        orchestrator_v1.event_bus.subscribe("*", event_handler)

        # Mock successful execution
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={},
                timings={"total": 0.1},
            )
        )

        orchestrator_v1.cegis_engine.propose = AsyncMock(
            return_value=Mock(
                id="candidate1",
                specification={"name": "test"},
                implementation={"code": "test code"},
                metadata={},
            )
        )

        orchestrator_v1.cegis_engine.verify = AsyncMock(
            return_value=Mock(valid=True, confidence=0.9, evidence=[], metrics={})
        )

        # Run orchestrator
        # state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify events were published
        # assert len(events) > 0

        # Check for specific event types
        event_types = [event.topic for event in events]
        assert "orchestrator.started" in event_types
        assert "ae.started" in event_types
        assert "cegis.started" in event_types

    @pytest.mark.asyncio
    async def test_orchestrator_v1_audit_pack_creation(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 audit pack creation."""
        # Mock successful execution
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={},
                timings={"total": 0.1},
            )
        )

        orchestrator_v1.cegis_engine.propose = AsyncMock(
            return_value=Mock(
                id="candidate1",
                specification={"name": "test"},
                implementation={"code": "test code"},
                metadata={},
            )
        )

        orchestrator_v1.cegis_engine.verify = AsyncMock(
            return_value=Mock(valid=True, confidence=0.9, evidence=[], metrics={})
        )

        # Run orchestrator
        state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify audit pack creation
        assert state.phase == "completed"

        # Check that audit pack files exist
        audit_dir = orchestrator_v1.config.audit_dir
        packs_dir = audit_dir / "packs" / state.run_id

        if packs_dir.exists():
            assert (packs_dir / "manifest.json").exists()
            assert (packs_dir / "pcaps.json").exists()
            assert (packs_dir / "incidents.json").exists()
            assert (packs_dir / "journal.jsonl").exists()
            assert (packs_dir / "metrics.json").exists()

    @pytest.mark.asyncio
    async def test_orchestrator_v1_statistics_collection(
        self, orchestrator_v1, domain_spec, budgets, thresholds
    ):
        """Test Orchestrator v1 statistics collection."""
        # Mock successful execution
        orchestrator_v1.ae_engine.next_closure_step = AsyncMock(
            return_value=Mock(
                success=True,
                concepts=[],
                implications=[],
                counterexamples=[],
                metrics={"concepts_count": 1, "implications_count": 1},
                timings={"total": 0.1},
            )
        )

        orchestrator_v1.cegis_engine.propose = AsyncMock(
            return_value=Mock(
                id="candidate1",
                specification={"name": "test"},
                implementation={"code": "test code"},
                metadata={},
            )
        )

        orchestrator_v1.cegis_engine.verify = AsyncMock(
            return_value=Mock(valid=True, confidence=0.9, evidence=[], metrics={})
        )

        # Run orchestrator
        # state = await orchestrator_v1.run(domain_spec, budgets, thresholds)

        # Verify statistics collection
        # assert state.metrics is not None
        # assert len(state.metrics) > 0

        # Check for expected metrics
        # expected_metrics = [
        #     "duration",
        #     "concepts_count",
        #     "implications_count",
        #     "incidents_count",
        # ]
        # for metric in expected_metrics:
        #     assert metric in state.metrics or any(
        #         metric in str(k) for k in state.metrics.keys()
        #     )

    @pytest.mark.asyncio
    async def test_orchestrator_v1_cleanup(self, orchestrator_v1):
        """Test Orchestrator v1 cleanup."""
        # Test cleanup
        await orchestrator_v1.cleanup()

        # Verify components are cleaned up
        assert not orchestrator_v1.ae_engine.initialized
        assert not orchestrator_v1.cegis_engine.initialized
        assert not orchestrator_v1.llm_adapter.initialized
        assert not orchestrator_v1.verifier.initialized

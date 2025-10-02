#!/usr/bin/env python3
"""
Demo script for Orchestrator v1 with real components.
Demonstrates end-to-end pipeline with actual engines, adapters, and schedulers.
"""

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from orchestrator.adapters.llm_adapter import LLMAdapter, LLMConfig
from orchestrator.adapters.verifier import VerificationConfig, Verifier
from orchestrator.engines.real_ae_engine import RealAEEngine
from orchestrator.engines.real_cegis_engine import RealCegisEngine
from orchestrator.orchestrator_v1 import OrchestratorV1, OrchestratorV1Config
from orchestrator.scheduler.async_scheduler import (AsyncScheduler,
                                                    SchedulerConfig)
from orchestrator.scheduler.budget_manager import BudgetConfig, BudgetManager
from pefc.events.structured_bus import StructuredEventBus


class MockOracleAdapter:
    """Mock oracle adapter for testing."""

    def __init__(self):
        self.verification_results = {}

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize oracle adapter."""
        pass

    async def verify_implication(self, implication: Dict[str, Any]) -> Any:
        """Verify implication."""
        # Mock verification - accept implications with "legal" in conclusions
        conclusions = implication.get("conclusion", [])
        has_legal = any("legal" in str(c).lower() for c in conclusions)

        if has_legal:
            return type(
                "OracleResult",
                (),
                {
                    "valid": True,
                    "attestation": {"type": "mock_verification"},
                    "evidence": ["mock_legal_check"],
                },
            )()
        else:
            return type(
                "OracleResult",
                (),
                {
                    "valid": False,
                    "counterexample": {
                        "id": f"mock_cex_{hash(str(implication))}",
                        "context": {"domain": "RegTech"},
                        "evidence": ["mock_violation"],
                        "violates_premise": False,
                        "violates_conclusion": True,
                        "explanation": "Mock counterexample",
                    },
                    "reason": "Mock verification failed",
                },
            )()


class MockBanditStrategy:
    """Mock bandit strategy for testing."""

    def __init__(self):
        self.selections = []

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize bandit strategy."""
        pass

    async def select(self, candidates: List[Dict[str, Any]], context: Any) -> Dict[str, Any]:
        """Select candidate using bandit strategy."""
        if candidates:
            selected = candidates[0]
            self.selections.append(selected)
            return selected
        return {}


class MockDiversityStrategy:
    """Mock diversity strategy for testing."""

    def __init__(self):
        self.selections = []

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize diversity strategy."""
        pass

    async def select_diverse_items(
        self, items: List[Dict[str, Any]], k: int
    ) -> List[Dict[str, Any]]:
        """Select diverse items."""
        selected = items[:k]
        self.selections.extend(selected)
        return selected


class MockSynthesisStrategy:
    """Mock synthesis strategy for testing."""

    def __init__(self):
        self.generations = []

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize synthesis strategy."""
        pass

    def get_name(self) -> str:
        """Get strategy name."""
        return "mock_synthesis"

    async def generate_candidate_specification(self, ctx: Any) -> Dict[str, Any]:
        """Generate candidate specification."""
        spec = {
            "name": f"candidate_{len(self.generations) + 1}",
            "properties": ["property1", "property2"],
            "constraints": ["constraint1"],
            "implementation_hints": ["hint1", "hint2"],
        }
        self.generations.append(spec)
        return spec


class MockRefinementStrategy:
    """Mock refinement strategy for testing."""

    def __init__(self):
        self.refinements = []

    async def initialize(self, domain_spec: Dict[str, Any]) -> None:
        """Initialize refinement strategy."""
        pass

    def get_name(self) -> str:
        """Get strategy name."""
        return "mock_refinement"

    async def refine_specification(
        self, original_spec: Dict[str, Any], counterexample: Any, context: Any
    ) -> Dict[str, Any]:
        """Refine specification based on counterexample."""
        refined_spec = {
            **original_spec,
            "refined": True,
            "counterexample_id": (
                counterexample.id if hasattr(counterexample, "id") else "unknown"
            ),
            "refinement_count": len(self.refinements) + 1,
        }
        self.refinements.append(refined_spec)
        return refined_spec


def setup_logging():
    """Setup structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("orchestrator_v1_demo.log"),
        ],
    )


def create_demo_domain_spec() -> Dict[str, Any]:
    """Create demo domain specification."""
    return {
        "id": "demo_regtech_v1",
        "name": "RegTech Compliance Demo v1",
        "objects": [
            "user_registration",
            "payment_processing",
            "data_encryption",
            "audit_logging",
            "access_control",
        ],
        "attributes": [
            "requires_authentication",
            "requires_authorization",
            "requires_encryption",
            "requires_audit",
            "requires_validation",
        ],
        "specification": {
            "requirements": [
                "All user actions must be authenticated",
                "All data must be encrypted in transit",
                "All operations must be audited",
                "All inputs must be validated",
            ],
            "constraints": [
                "Authentication must use strong passwords",
                "Encryption must use AES-256",
                "Audit logs must be immutable",
                "Validation must be server-side",
            ],
        },
        "constraints": [
            {
                "type": "security_constraint",
                "condition": "authentication_required",
                "severity": "high",
            },
            {
                "type": "privacy_constraint",
                "condition": "encryption_required",
                "severity": "critical",
            },
            {
                "type": "compliance_constraint",
                "condition": "audit_required",
                "severity": "high",
            },
        ],
    }


def create_demo_budgets() -> Dict[str, Any]:
    """Create demo budgets."""
    return {
        "ae_timeout": 10.0,
        "cegis_timeout": 20.0,
        "llm_max_tokens": 1024,
        "llm_temperature": 0.1,
        "verify_timeout": 10.0,
        "total_budget": 120.0,
        "time": 60.0,
        "tokens": 10000,
        "api_calls": 50,
    }


def create_demo_thresholds() -> Dict[str, Any]:
    """Create demo thresholds."""
    return {
        "min_confidence": 0.8,
        "max_iterations": 8,
        "success_rate": 0.9,
        "min_concepts": 3,
        "max_incidents": 5,
        "convergence_threshold": 0.95,
    }


async def run_demo():
    """Run the complete Orchestrator v1 demo."""
    print("🚀 Démarrage de la démonstration Orchestrateur v1")
    print("=" * 60)

    # Setup
    setup_logging()

    # Create temporary directory for audit
    temp_dir = tempfile.mkdtemp(prefix="orchestrator_v1_demo_")
    print(f"📁 Répertoire d'audit temporaire: {temp_dir}")

    try:
        # Create configuration
        config = OrchestratorV1Config(
            ae_timeout=10.0,
            cegis_propose_timeout=5.0,
            cegis_verify_timeout=5.0,
            cegis_refine_timeout=5.0,
            cegis_max_iterations=5,
            audit_dir=temp_dir,
            enable_budget_management=True,
            enable_async_scheduler=True,
            enable_failreason_emission=True,
            llm_api_url="https://api.openai.com/v1/chat/completions",
            llm_api_key="demo_key",
            llm_model="gpt-4",
            llm_max_tokens=1024,
            llm_temperature=0.1,
        )

        # Create real components
        llm_config = LLMConfig(
            api_url=config.llm_api_url,
            api_key=config.llm_api_key,
            model=config.llm_model,
            max_tokens=config.llm_max_tokens,
            temperature=config.llm_temperature,
            timeout=10.0,
            max_retries=2,
            concurrent_requests=3,
        )

        verifier_config = VerificationConfig(
            timeout=config.verifier_timeout,
            max_retries=2,
            concurrent_verifications=3,
            tools=["static_analysis", "property_check", "test_execution"],
        )

        scheduler_config = SchedulerConfig(
            max_concurrent_tasks=config.max_concurrent_tasks,
            default_timeout=config.scheduler_timeout,
            max_retries=2,
            enable_budget_management=True,
        )

        budget_config = BudgetConfig(
            default_timeout=30.0,
            warning_threshold=config.budget_warning_threshold,
            critical_threshold=config.budget_critical_threshold,
            overrun_threshold=config.budget_overrun_threshold,
        )

        # Create adapters
        llm_adapter = LLMAdapter(llm_config)
        verifier = Verifier(verifier_config)
        scheduler = AsyncScheduler(scheduler_config)
        budget_manager = BudgetManager(budget_config)
        event_bus = StructuredEventBus()

        # Create mock strategies
        oracle_adapter = MockOracleAdapter()
        bandit_strategy = MockBanditStrategy()
        diversity_strategy = MockDiversityStrategy()
        synthesis_strategy = MockSynthesisStrategy()
        refinement_strategy = MockRefinementStrategy()

        # Create engines
        ae_engine = RealAEEngine(
            oracle_adapter=oracle_adapter,
            bandit_strategy=bandit_strategy,
            diversity_strategy=diversity_strategy,
        )

        cegis_engine = RealCegisEngine(
            llm_adapter=llm_adapter,
            verifier=verifier,
            synthesis_strategy=synthesis_strategy,
            refinement_strategy=refinement_strategy,
        )

        # Create orchestrator v1
        orchestrator = OrchestratorV1(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=llm_adapter,
            verifier=verifier,
            scheduler=scheduler,
            budget_manager=budget_manager,
            event_bus=event_bus,
        )

        print("✅ Orchestrateur v1 initialisé")

        # Create domain specification
        domain_spec = create_demo_domain_spec()
        budgets = create_demo_budgets()
        thresholds = create_demo_thresholds()

        print(f"📋 Domaine: {domain_spec['name']}")
        print(f"🎯 Objets: {len(domain_spec['objects'])}")
        print(f"🔍 Attributs: {len(domain_spec['attributes'])}")
        print(f"📝 Contraintes: {len(domain_spec['constraints'])}")

        # Track events
        events = []

        def event_handler(event):
            events.append(event)
            print(f"📡 Événement: {event.topic}")

        event_bus.subscribe("*", event_handler)

        # Run orchestrator v1
        print("\n🔄 Exécution de l'Orchestrateur v1...")
        start_time = datetime.now()

        state = await orchestrator.run(domain_spec, budgets, thresholds)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Orchestrateur v1 terminé en {duration:.2f}s")
        print(f"📊 Phase: {state.phase}")
        print(f"🆔 Run ID: {state.run_id}")
        print(f"🔗 Trace ID: {state.trace_id}")

        # Display results
        print("\n📈 Résultats AE:")
        print(f"  - Concepts: {len(state.ae_results)}")
        if state.ae_results:
            for i, result in enumerate(state.ae_results):
                print(
                    f"    {i+1}. Concepts: {len(result.concepts)}, Implications: {len(result.implications)}"
                )

        print("\n🔧 Résultats CEGIS:")
        print(f"  - Candidats: {len(state.cegis_results)}")
        if state.cegis_results:
            for i, result in enumerate(state.cegis_results):
                print(f"    {i+1}. Candidat: {result.candidate.id}, Vérifié: {result.success}")

        print("\n⚠️ Incidents:")
        print(f"  - Total: {len(state.incidents)}")
        for incident in state.incidents:
            print(f"    - {incident.type}: {incident.severity}")

        print("\n📦 PCAPs:")
        print(f"  - Total: {len(state.pcaps)}")
        for pcap in state.pcaps:
            print(f"    - {pcap.action}: {pcap.context_hash[:8]}...")

        print("\n📊 Métriques:")
        for key, value in state.metrics.items():
            print(f"  - {key}: {value}")

        print("\n📡 Événements:")
        print(f"  - Total: {len(events)}")
        event_types = {}
        for event in events:
            event_type = event.topic.split(".")[0]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for event_type, count in event_types.items():
            print(f"    - {event_type}: {count}")

        # Display audit pack
        audit_dir = Path(temp_dir)
        packs_dir = audit_dir / "packs" / state.run_id

        if packs_dir.exists():
            print("\n📁 Audit Pack créé:")
            print(f"  - Répertoire: {packs_dir}")

            for file_path in packs_dir.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    print(f"    - {file_path.name}: {size} bytes")

        # Display component statistics
        print("\n🔧 Statistiques des composants:")

        # LLM Adapter stats
        llm_stats = await llm_adapter.get_statistics()
        print("  - LLM Adapter:")
        print(f"    - Requêtes: {llm_stats['total_requests']}")
        print(f"    - Succès: {llm_stats['successful_requests']}")
        print(f"    - Taux de succès: {llm_stats['success_rate']:.2%}")

        # Verifier stats
        verifier_stats = await verifier.get_statistics()
        print("  - Verifier:")
        print(f"    - Vérifications: {verifier_stats['total_verifications']}")
        print(f"    - Succès: {verifier_stats['successful_verifications']}")
        print(f"    - Taux de succès: {verifier_stats['success_rate']:.2%}")

        # Scheduler stats
        scheduler_status = await scheduler.get_status()
        print("  - Scheduler:")
        print(f"    - Tâches totales: {scheduler_status['stats']['total_tasks']}")
        print(f"    - Tâches complétées: {scheduler_status['stats']['completed_tasks']}")
        print(f"    - Tâches échouées: {scheduler_status['stats']['failed_tasks']}")

        # Budget manager stats
        if config.enable_budget_management:
            budget_status = await budget_manager.get_status()
            print("  - Budget Manager:")
            for budget_type, status in budget_status["budgets"].items():
                print(
                    f"    - {budget_type}: {status['current']:.2f}/{status['limit']:.2f} ({status['percentage']:.1%})"
                )

        print("\n🎯 Démonstration Orchestrateur v1 terminée avec succès!")
        print(f"📁 Fichiers d'audit disponibles dans: {temp_dir}")

        return state

    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback

        traceback.print_exc()
        raise

    finally:
        # Cleanup
        try:
            await orchestrator.cleanup()
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")


if __name__ == "__main__":
    asyncio.run(run_demo())

#!/usr/bin/env python3
"""
Demo script for industrialised Orchestrator (AE/CEGIS).
Demonstrates end-to-end pipeline with real Next-Closure and CEGIS engines.
"""

import asyncio
import json
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from orchestrator.orchestrator import Orchestrator
from orchestrator.config import OrchestratorConfig
from orchestrator.engines.next_closure_engine import NextClosureEngine
from orchestrator.engines.cegis_async_engine import AsyncCegisEngine
from pefc.events.structured_bus import StructuredEventBus


class DemoLLMAdapter:
    """Demo LLM adapter for synthesis."""

    def __init__(self):
        self.call_count = 0

    async def generate(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1) -> str:
        """Generate synthesis candidate."""
        self.call_count += 1

        # Mock synthesis based on prompt content
        if "synthesize" in prompt.lower():
            return json.dumps(
                {
                    "name": f"candidate_{self.call_count}",
                    "properties": ["property1", "property2"],
                    "constraints": ["constraint1"],
                    "implementation_hints": ["hint1", "hint2"],
                }
            )
        elif "refine" in prompt.lower():
            return json.dumps(
                {
                    "name": f"refined_candidate_{self.call_count}",
                    "properties": ["property1", "property2", "property3"],
                    "constraints": ["constraint1", "constraint2"],
                    "implementation_hints": ["hint1", "hint2", "hint3"],
                }
            )
        else:
            return json.dumps(
                {
                    "name": f"generated_{self.call_count}",
                    "properties": ["default_property"],
                    "constraints": [],
                    "implementation_hints": [],
                }
            )


class DemoVerifier:
    """Demo verifier for CEGIS."""

    def __init__(self, success_rate: float = 0.7):
        self.success_rate = success_rate
        self.verify_count = 0

    async def verify(
        self,
        specification: Dict[str, Any],
        implementation: Dict[str, Any],
        constraints: list,
    ) -> Dict[str, Any]:
        """Verify implementation against specification."""
        self.verify_count += 1

        # Simulate verification with success rate
        import random

        is_valid = random.random() < self.success_rate

        if is_valid:
            return {
                "valid": True,
                "confidence": 0.9,
                "evidence": [
                    {"type": "static_analysis", "result": "passed"},
                    {"type": "property_check", "result": "satisfied"},
                ],
                "metrics": {"verification_time": 0.1, "checks_performed": 5},
            }
        else:
            return {
                "valid": False,
                "failing_property": "property_check",
                "evidence": {
                    "error": "Property violation detected",
                    "line": 42,
                    "condition": "assert condition",
                },
                "suggestions": [
                    "Add null check",
                    "Verify input bounds",
                    "Check preconditions",
                ],
            }


def setup_logging():
    """Setup structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("demo_orchestrator.log"),
        ],
    )

    # Enable JSON logging for events
    event_logger = logging.getLogger("orchestrator.events")
    event_logger.setLevel(logging.INFO)


def create_demo_domain_spec() -> Dict[str, Any]:
    """Create demo domain specification."""
    return {
        "id": "demo_regtech",
        "name": "RegTech Code Compliance",
        "description": "Regulatory technology code compliance domain",
        "objects": [
            "api_endpoint_1",
            "api_endpoint_2",
            "api_endpoint_3",
            "api_endpoint_4",
            "api_endpoint_5",
        ],
        "attributes": [
            "requires_authentication",
            "requires_authorization",
            "requires_audit_logging",
            "requires_data_encryption",
            "requires_input_validation",
        ],
        "specification": {
            "requirements": [
                "All API endpoints must require authentication",
                "All API endpoints must require authorization",
                "All API endpoints must log audit events",
                "All API endpoints must encrypt sensitive data",
                "All API endpoints must validate input",
            ],
            "constraints": [
                "Authentication must be OAuth2",
                "Authorization must be role-based",
                "Audit logs must be immutable",
                "Encryption must be AES-256",
                "Input validation must be strict",
            ],
        },
        "constraints": [
            {
                "type": "security_constraint",
                "condition": "authentication_required",
                "severity": "high",
            },
            {
                "type": "compliance_constraint",
                "condition": "audit_logging_required",
                "severity": "medium",
            },
        ],
    }


def create_demo_budgets() -> Dict[str, Any]:
    """Create demo budgets."""
    return {
        "ae_timeout": 30.0,
        "cegis_timeout": 60.0,
        "llm_max_tokens": 2048,
        "llm_temperature": 0.1,
        "verify_timeout": 15.0,
        "total_budget": 300.0,  # 5 minutes total
    }


def create_demo_thresholds() -> Dict[str, Any]:
    """Create demo thresholds."""
    return {
        "min_confidence": 0.8,
        "max_iterations": 10,
        "success_rate": 0.9,
        "min_concepts": 3,
        "max_incidents": 5,
    }


async def run_demo():
    """Run the complete demo."""
    print("🚀 Démarrage de la démonstration Orchestrateur Industrialisé")
    print("=" * 60)

    # Setup
    setup_logging()

    # Create temporary directory for audit
    temp_dir = tempfile.mkdtemp(prefix="orchestrator_demo_")
    print(f"📁 Répertoire d'audit temporaire: {temp_dir}")

    try:
        # Create configuration
        config = OrchestratorConfig(
            ae_timeout=30.0,
            cegis_propose_timeout=10.0,
            cegis_verify_timeout=15.0,
            cegis_refine_timeout=10.0,
            cegis_max_iterations=8,
            cegis_max_stable_no_improve=3,
            audit_dir=temp_dir,
            hermetic_mode=True,
        )

        # Create components
        llm_adapter = DemoLLMAdapter()
        verifier = DemoVerifier(success_rate=0.6)  # 60% success rate
        event_bus = StructuredEventBus()

        # Create engines
        ae_engine = NextClosureEngine()
        cegis_engine = AsyncCegisEngine(llm_adapter, verifier)

        # Create orchestrator
        orchestrator = Orchestrator(
            config=config,
            ae_engine=ae_engine,
            cegis_engine=cegis_engine,
            llm_adapter=llm_adapter,
            verifier=verifier,
            event_bus=event_bus,
        )

        print("✅ Orchestrateur initialisé")

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

        # Run orchestrator
        print("\n🔄 Exécution de la pipeline AE/CEGIS...")
        start_time = datetime.now()

        state = await orchestrator.run(domain_spec, budgets, thresholds)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Pipeline terminée en {duration:.2f}s")
        print(f"🆔 Run ID: {state.run_id}")
        print(f"🔗 Trace ID: {state.trace_id}")
        print(f"📊 Phase finale: {state.phase}")

        # Display results
        print("\n📊 RÉSULTATS:")
        print("-" * 40)

        # AE Results
        print(f"🔍 AE - Concepts générés: {len(state.ae_results)}")
        for i, result in enumerate(state.ae_results):
            if result.success:
                print(
                    f"  ✓ Étape {i+1}: {len(result.concepts)} concepts, {len(result.implications)} implications"
                )
            else:
                print(f"  ✗ Étape {i+1}: Échec - {result.error}")

        # CEGIS Results
        print(f"🔄 CEGIS - Itérations: {len(state.cegis_results)}")
        for i, result in enumerate(state.cegis_results):
            if result.success:
                print(f"  ✓ Itération {i+1}: Candidat {result.candidate.id} vérifié")
            else:
                print(f"  ✗ Itération {i+1}: Échec - {result.error}")

        # Incidents
        print(f"⚠️  Incidents: {len(state.incidents)}")
        for incident in state.incidents:
            print(f"  - {incident.type} ({incident.severity}): {incident.context}")

        # Metrics
        print(f"📈 Métriques: {len(state.metrics)}")
        for key, value in state.metrics.items():
            print(f"  - {key}: {value}")

        # Events
        print(f"📡 Événements publiés: {len(events)}")
        event_types = {}
        for event in events:
            event_types[event.topic] = event_types.get(event.topic, 0) + 1

        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")

        # Audit Pack
        print("\n📦 AUDIT PACK:")
        print("-" * 40)

        audit_dir = Path(temp_dir)
        packs_dir = audit_dir / "packs" / state.run_id

        if packs_dir.exists():
            print(f"📁 Répertoire: {packs_dir}")

            # Check files
            files = list(packs_dir.glob("*"))
            for file_path in files:
                size = file_path.stat().st_size if file_path.is_file() else 0
                print(f"  📄 {file_path.name}: {size} bytes")

            # Check ZIP file
            zip_file = audit_dir / "packs" / f"{state.run_id}.zip"
            if zip_file.exists():
                zip_size = zip_file.stat().st_size
                print(f"  📦 {zip_file.name}: {zip_size} bytes")

            # Verify audit pack
            verification = await orchestrator.audit_pack_builder.verify_audit_pack(state.run_id)
            if verification["valid"]:
                print("  ✅ Audit pack valide")
                print(f"  🔐 SHA256: {verification['sha256'][:16]}...")
                print(f"  🌳 Merkle: {verification['merkle_root'][:16]}...")
            else:
                print(f"  ❌ Audit pack invalide: {verification['error']}")

        # Final verdict
        print("\n🎯 VERDICT FINAL:")
        print("-" * 40)

        if state.phase == "completed":
            if len(state.cegis_results) > 0 and state.cegis_results[-1].success:
                print("✅ SUCCÈS: Solution CEGIS trouvée")
                print(f"   Candidat final: {state.cegis_results[-1].candidate.id}")
                print(f"   Confiance: {state.cegis_results[-1].verdict.confidence}")
            else:
                print("⚠️  PARTIEL: AE réussi, CEGIS partiel")
                print(f"   Concepts: {sum(len(r.concepts) for r in state.ae_results if r.success)}")
                print(f"   Incidents: {len(state.incidents)}")
        else:
            print("❌ ÉCHEC: Pipeline interrompue")
            print(f"   Phase: {state.phase}")
            print(f"   Incidents: {len(state.incidents)}")

        print("\n📊 RÉSUMÉ:")
        print(f"   Durée: {duration:.2f}s")
        print(f"   Événements: {len(events)}")
        print(f"   Audit pack: {'✅' if packs_dir.exists() else '❌'}")
        print(f"   Verdict: {'✅' if state.phase == 'completed' else '❌'}")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🧹 Nettoyage...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("✅ Démonstration terminée")


if __name__ == "__main__":
    print("🎯 Démonstration Orchestrateur Industrialisé (AE/CEGIS)")
    print("=" * 60)
    print("Pipeline: Next-Closure (FCA) → CEGIS → Audit Pack")
    print("Fonctionnalités: Événements structurés, PCAP, Incidents")
    print("=" * 60)

    asyncio.run(run_demo())

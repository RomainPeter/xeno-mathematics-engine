#!/usr/bin/env python3
"""
Demo script for Architecture Unifiée v0.1.
Demonstrates AE + CEGIS loops with RegTech/Code domain.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proofengine.orchestrator.unified_orchestrator import (
    UnifiedOrchestrator,
    ExplorationConfig,
)
from proofengine.core.egraph import EGraph, canonicalize_state


async def demo_unified_architecture():
    """Demonstrate the unified architecture v0.1."""
    print("🚀 Architecture Unifiée v0.1 Demo")
    print("=" * 50)

    # Load domain specification
    domain_spec_path = project_root / "specs" / "v0.1" / "domain-spec-regtech-code.json"
    with open(domain_spec_path, "r") as f:
        domain_spec = json.load(f)

    print(f"📋 Domain: {domain_spec['domain']}")
    print(f"🔒 Closure: {domain_spec['closure']}")
    print(f"🔍 Oracle endpoints: {len(domain_spec['oracle_endpoints'])}")

    # Create exploration configuration
    config = ExplorationConfig(
        domain_spec=domain_spec,
        budget={
            "time_ms": 30000,  # 30 seconds
            "audit_cost": 1000,  # $1000
            "legal_risk": 0.3,  # 30% risk
            "tech_debt": 0.2,  # 20% tech debt
        },
        diversity_config={"target_diversity": 0.8, "min_novelty": 0.6},
        selection_strategy="bandit",
        max_iterations=5,
        convergence_threshold=0.1,
    )

    print(f"💰 Budget: {config.budget}")
    print(f"🎯 Selection: {config.selection_strategy}")
    print(f"🔄 Max iterations: {config.max_iterations}")

    # Initialize orchestrator
    orchestrator = UnifiedOrchestrator(config)

    # Create initial cognitive state
    initial_state = {
        "H": [  # Hypotheses
            {
                "id": "h1",
                "title": "License compliance",
                "body": "Open source projects need proper licensing",
                "status": "open",
                "evidence_ids": [],
                "created_at": datetime.now().isoformat(),
            }
        ],
        "E": [  # Evidence
            {
                "id": "e1",
                "kind": "code",
                "uri": "src/main.py",
                "hash": "abc123...",
                "provenance": "git commit",
                "created_at": datetime.now().isoformat(),
            }
        ],
        "K": [  # Constraints
            {
                "id": "k1",
                "source": "eu_ai_act",
                "rule": "transparency_required",
                "severity": "high",
                "tags": ["compliance"],
            }
        ],
        "A": [  # Artifacts
            {
                "id": "a1",
                "type": "code_change",
                "ref_ids": ["e1"],
                "produced_by_journal_id": "j1",
            }
        ],
        "J": {"version": "0.1.0", "entries": []},  # Journal
        "Sigma": {  # Seed/Environment
            "repo": "proof-engine",
            "branch": "main",
            "commit": "abc123...",
            "tooling": {"python": "3.9", "llm_model": "gpt-4"},
        },
    }

    print(
        f"🧠 Initial state: {len(initial_state['H'])} hypotheses, {len(initial_state['E'])} evidence"
    )

    # Canonicalize initial state
    egraph = EGraph()
    canonical_id = canonicalize_state(initial_state, egraph)
    print(f"🔗 Canonical state ID: {canonical_id}")

    # Run exploration
    print("\n🔄 Starting exploration...")
    try:
        results = await orchestrator.explore(initial_state)

        print("\n✅ Exploration completed!")
        print("📊 Results summary:")
        print(
            f"   - Implications accepted: {len(results.get('ae_results', {}).get('iteration_0', {}).get('implications_accepted', []))}"
        )
        print(
            f"   - Choreographies accepted: {len(results.get('cegis_results', {}).get('iteration_0', {}).get('accepted_choreographies', []))}"
        )
        print(
            f"   - Counterexamples: {len(results.get('ae_results', {}).get('iteration_0', {}).get('counterexamples', []))}"
        )
        print(f"   - Incidents: {len(results.get('incidents', []))}")

        # Show performance metrics
        metrics = results.get("performance_metrics", {})
        print("\n📈 Performance metrics:")
        print(f"   - Total implications: {metrics.get('total_implications', 0)}")
        print(f"   - Total choreographies: {metrics.get('total_choreographies', 0)}")
        print(f"   - Total counterexamples: {metrics.get('total_counterexamples', 0)}")
        print(
            f"   - E-graph classes: {metrics.get('egraph_stats', {}).get('total_classes', 0)}"
        )

        # Show artifacts
        artifacts = results.get("artifacts", [])
        print(f"\n📦 Generated artifacts: {len(artifacts)}")
        for artifact in artifacts[:3]:  # Show first 3
            print(f"   - {artifact['type']}: {artifact['id']}")

        # Save results
        output_dir = project_root / "out" / "unified_architecture_demo"
        output_dir.mkdir(parents=True, exist_ok=True)

        results_file = (
            output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {results_file}")

        return results

    except Exception as e:
        print(f"\n❌ Exploration failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def demo_egraph_canonicalization():
    """Demonstrate e-graph canonicalization."""
    print("\n🔗 E-graph Canonicalization Demo")
    print("=" * 40)

    egraph = EGraph()

    # Test state canonicalization
    state1 = {"H": [{"id": "h1", "title": "Test"}], "E": [], "K": []}
    state2 = {"H": [{"id": "h1", "title": "Test"}], "E": [], "K": []}  # Same as state1
    state3 = {"H": [{"id": "h2", "title": "Different"}], "E": [], "K": []}  # Different

    id1 = canonicalize_state(state1, egraph)
    id2 = canonicalize_state(state2, egraph)
    id3 = canonicalize_state(state3, egraph)

    print(f"State 1 canonical ID: {id1}")
    print(f"State 2 canonical ID: {id2}")
    print(f"State 3 canonical ID: {id3}")
    print(f"States 1&2 equivalent: {id1 == id2}")
    print(f"States 1&3 equivalent: {id1 == id3}")

    # Show e-graph stats
    stats = egraph.get_stats()
    print("\n📊 E-graph stats:")
    print(f"   - Total nodes: {stats['total_nodes']}")
    print(f"   - Total classes: {stats['total_classes']}")
    print(f"   - Avg class size: {stats['avg_class_size']:.2f}")


async def demo_schemas_validation():
    """Demonstrate schema validation."""
    print("\n📋 Schema Validation Demo")
    print("=" * 40)

    # Test DCA schema
    dca_example = {
        "version": "0.1.0",
        "id": "dca_1",
        "type": "AE_query",
        "context_hash": "a" * 64,
        "query_or_prog": "has_license ∧ is_open_source ⇒ compliance_ok",
        "V_hat": {
            "time_ms": 100,
            "audit_cost": 50,
            "legal_risk": 0.1,
            "tech_debt": 0.2,
        },
        "S_hat": {
            "info_gain": 0.8,
            "coverage_gain": 0.7,
            "MDL_drop": -0.3,
            "novelty": 0.6,
        },
        "V_actual": {
            "time_ms": 120,
            "audit_cost": 55,
            "legal_risk": 0.1,
            "tech_debt": 0.2,
        },
        "S_actual": {
            "info_gain": 0.8,
            "coverage_gain": 0.7,
            "MDL_drop": -0.3,
            "novelty": 0.6,
        },
        "verdict": "accept",
    }

    print(f"✅ DCA example created: {dca_example['id']}")
    print(f"   - Type: {dca_example['type']}")
    print(f"   - Query: {dca_example['query_or_prog']}")
    print(f"   - Verdict: {dca_example['verdict']}")

    # Test CompositeOp schema
    composite_example = {
        "version": "0.1.0",
        "id": "choreo_1",
        "ops": ["Meet", "Verify", "Normalize"],
        "guards": ["K1", "K2"],
        "budgets": {
            "time_ms": 1000,
            "audit_cost": 50,
            "legal_risk": 0.1,
            "tech_debt": 0.2,
        },
        "diversity_keys": ["constraint_focus", "verification_heavy"],
        "rationale": "Basic constraint checking approach",
    }

    print(f"\n✅ CompositeOp example created: {composite_example['id']}")
    print(f"   - Operations: {composite_example['ops']}")
    print(f"   - Guards: {composite_example['guards']}")
    print(f"   - Rationale: {composite_example['rationale']}")


async def main():
    """Main demo function."""
    print("🎯 Architecture Unifiée v0.1 - Complete Demo")
    print("=" * 60)

    # Demo 1: Schema validation
    await demo_schemas_validation()

    # Demo 2: E-graph canonicalization
    await demo_egraph_canonicalization()

    # Demo 3: Full unified architecture
    await demo_unified_architecture()

    print("\n🎉 Demo completed successfully!")
    print("\n📚 Next steps:")
    print("   1. Review generated artifacts in out/unified_architecture_demo/")
    print("   2. Test with real RegTech/Code scenarios")
    print("   3. Integrate with actual OPA/static analysis tools")
    print("   4. Scale to larger exploration spaces")


if __name__ == "__main__":
    asyncio.run(main())

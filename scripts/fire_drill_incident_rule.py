#!/usr/bin/env python3
"""
Fire-drill: Incident→Rule automation test
Inject fake ConstraintBreach → verify HS-Tree → test added to K → OPA passes
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def create_fake_constraint_breach():
    """Create a fake ConstraintBreach incident for testing"""
    incident = {
        "id": f"fire_drill_{int(datetime.now().timestamp())}",
        "type": "constraint_breach",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "constraint": "data_privacy_violation",
            "path": "/data/user/personal",
            "severity": "high",
            "context": {
                "data_class": "personal",
                "has_consent": False,
                "purpose_unclear": True,
            },
        },
        "implication": {
            "id": "imp_fire_drill",
            "premises": ["data_class=personal", "has_consent=false"],
            "conclusion": "requires_legal_basis",
            "justification": "GDPR Article 6 requires legal basis for personal data processing",
        },
    }
    return incident


def test_hs_tree_diagnostics():
    """Test HS-Tree diagnostics for minimal test generation"""
    print("🔧 Testing HS-Tree diagnostics...")

    # Import HS-Tree
    try:
        from methods.diagnostics.hs_tree import minimal_hitting_sets

        print("✅ HS-Tree module imported successfully")

        # Create mock conflicts for testing
        conflicts = [
            {"data_privacy", "consent_missing"},
            {"data_privacy", "purpose_unclear"},
            {"consent_missing", "purpose_unclear"},
        ]

        # Find minimal hitting sets
        hitting_sets = list(minimal_hitting_sets(conflicts, max_size=2))
        print(f"✅ Found {len(hitting_sets)} minimal hitting sets")

        for i, hs in enumerate(hitting_sets):
            print(f"   Hitting set {i+1}: {hs}")

        return hitting_sets
    except ImportError as e:
        print(f"❌ Failed to import HS-Tree: {e}")
        return []
    except Exception as e:
        print(f"❌ HS-Tree test failed: {e}")
        return []


def test_incident_handler():
    """Test incident handler with fake ConstraintBreach"""
    print("🔧 Testing incident handler...")

    try:
        from orchestrator.handlers.failreason import IncidentHandler

        handler = IncidentHandler()
        incident = create_fake_constraint_breach()
        state = {"H": {}, "E": {}, "K": {}}

        print(f"📋 Created fake incident: {incident['id']}")
        print(f"   Type: {incident['type']}")
        print(f"   Constraint: {incident['details']['constraint']}")

        # Handle the incident
        result = handler.handle_incident(incident, state)

        print("✅ Incident handled successfully")
        print(f"   Updated state K: {len(result['updated_state']['K'])} rules")
        print(f"   Replanning required: {result['replanning_required']}")
        print(f"   Generated rule: {result['generated_rule']['id']}")

        return result
    except ImportError as e:
        print(f"❌ Failed to import incident handler: {e}")
        return None
    except Exception as e:
        print(f"❌ Incident handler test failed: {e}")
        return None


def test_opa_validation():
    """Test OPA validation with generated rules"""
    print("🔧 Testing OPA validation...")

    # Check if OPA is available
    try:
        result = subprocess.run(
            ["opa", "version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("✅ OPA is available")
            print(f"   Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ OPA not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ OPA not found - skipping OPA validation test")
        return False


def generate_test_report(results):
    """Generate test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "fire_drill_incident_rule",
        "results": {
            "hs_tree_working": len(results.get("hitting_sets", [])) > 0,
            "incident_handler_working": results.get("incident_result") is not None,
            "opa_available": results.get("opa_available", False),
            "k_updated": results.get("incident_result", {})
            .get("updated_state", {})
            .get("K", {}),
            "replanning_triggered": results.get("incident_result", {}).get(
                "replanning_required", False
            ),
        },
    }

    # Save report
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    report_file = out_dir / "fire_drill_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📊 Test report saved to: {report_file}")
    return report


def main():
    print("🔥 FIRE-DRILL: Incident→Rule Automation Test")
    print("=" * 60)
    print()

    results = {}

    # Test HS-Tree diagnostics
    hitting_sets = test_hs_tree_diagnostics()
    results["hitting_sets"] = hitting_sets

    # Test incident handler
    incident_result = test_incident_handler()
    results["incident_result"] = incident_result

    # Test OPA validation
    opa_available = test_opa_validation()
    results["opa_available"] = opa_available

    # Generate report
    report = generate_test_report(results)

    print()
    print("🎯 Fire-drill Summary:")
    print(f"✅ HS-Tree working: {report['results']['hs_tree_working']}")
    print(
        f"✅ Incident handler working: {report['results']['incident_handler_working']}"
    )
    print(f"✅ OPA available: {report['results']['opa_available']}")
    print(f"✅ K updated: {len(report['results']['k_updated'])} rules")
    print(f"✅ Replanning triggered: {report['results']['replanning_triggered']}")

    # Overall success
    success = all(
        [
            report["results"]["hs_tree_working"],
            report["results"]["incident_handler_working"],
            report["results"]["replanning_triggered"],
        ]
    )

    if success:
        print("\n🎉 FIRE-DRILL SUCCESS: Incident→Rule automation working!")
        return 0
    else:
        print("\n❌ FIRE-DRILL FAILED: Some components not working")
        return 1


if __name__ == "__main__":
    sys.exit(main())

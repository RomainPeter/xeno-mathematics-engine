#!/usr/bin/env python3
"""
Orchestrator skeleton v0.1 - Plan-Execute-Replan loop
Loads X + Π + FailReason, executes steps, updates state
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
import uuid

# Import LLM adapter
from adapter_llm import OrchestratorLLMAdapter


class OrchestratorError(Exception):
    pass


class Orchestrator:
    def __init__(self, plan_path, state_path, llm_adapter=None, verifier_mode="local"):
        self.plan_path = Path(plan_path)
        self.state_path = Path(state_path)
        self.plan = None
        self.state = None
        self.llm_adapter = llm_adapter or OrchestratorLLMAdapter()
        self.verifier_mode = verifier_mode
        self.metrics = {
            "accept_rate": 0.0,
            "replans_count": 0,
            "time_ms": 0,
            "steps_executed": 0,
        }

    def load_state(self):
        """Load plan and state from files"""
        with open(self.plan_path, "r", encoding="utf-8") as f:
            self.plan = json.load(f)

        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)

        print(f"Loaded plan: {self.plan['id']} - {self.plan['goal']}")
        print(
            f"Loaded state: {len(self.state['H'])} hypotheses, {len(self.state['E'])} evidence"
        )

    def execute_step(self, step):
        """Execute a single step"""
        print(f"Executing step: {step['id']} ({step['operator']})")

        # Generate PCAP for this step
        pcap = self.generate_pcap(step)

        # Verify PCAP
        verdict = self.verify_pcap(pcap)

        # Update state based on verdict
        if verdict == "accepted":
            self.update_state_accepted(step, pcap)
            self.metrics["steps_executed"] += 1
            return True
        else:
            self.handle_failure(step, pcap)
            return False

    def generate_pcap(self, step):
        """Generate PCAP for step (stub implementation)"""
        pcap_id = f"pcap-{uuid.uuid4().hex[:8]}"
        context_hash = hashlib.sha256(
            f"{step['operator']}:{step.get('input_refs', [])}".encode()
        ).hexdigest()

        # Mock action based on operator
        action_name = self.get_action_name(step["operator"])
        target = (
            step.get("input_refs", ["unknown"])[0]
            if step.get("input_refs")
            else "unknown"
        )

        pcap = {
            "version": "0.1.0",
            "id": pcap_id,
            "action": {
                "name": action_name,
                "params": step.get("params", {}),
                "target": target,
            },
            "context_hash": context_hash,
            "obligations": self.get_obligations_for_step(step),
            "justification": {
                "time_ms": 100,  # Mock timing
                "audit_cost": 0.1,
                "security_risk": 0.0,
                "info_loss": 0.0,
                "tech_debt": 0.0,
            },
            "proofs": self.generate_proofs(step),
        }

        return pcap

    def get_action_name(self, operator):
        """Map operator to action name"""
        mapping = {
            "Meet": "synthesize_design",
            "Refute": "analyze_evidence",
            "Generalize": "create_specification",
            "Specialize": "implement_solution",
            "Contrast": "compare_alternatives",
            "Normalize": "standardize_format",
            "Verify": "validate_implementation",
        }
        return mapping.get(operator, "unknown_action")

    def get_obligations_for_step(self, step):
        """Get obligations for step"""
        # Mock: return relevant constraints from state
        obligations = []
        for constraint in self.state.get("K", []):
            if constraint.get("severity") in ["high", "critical"]:
                obligations.append(constraint["id"])
        return obligations

    def generate_proofs(self, step):
        """Generate proofs for step"""
        proofs = []

        if step["operator"] == "Verify":
            proofs.append(
                {
                    "id": f"p-{uuid.uuid4().hex[:4]}",
                    "type": "unit_test",
                    "runner": "pytest",
                    "args": ["tests/", "-v"],
                    "expect": "all pass",
                }
            )

        if step["operator"] in ["Meet", "Generalize"]:
            proofs.append(
                {
                    "id": f"p-{uuid.uuid4().hex[:4]}",
                    "type": "static_analysis",
                    "runner": "ruff",
                    "args": ["--check", "."],
                    "expect": "clean",
                }
            )

        return proofs

    def verify_pcap(self, pcap):
        """Verify PCAP using specified verifier mode"""
        if self.verifier_mode == "docker":
            return self._verify_pcap_docker(pcap)
        else:
            return self._verify_pcap_local(pcap)

    def _verify_pcap_local(self, pcap):
        """Verify PCAP using local verifier"""
        # Mock verification: 70% success rate
        import random

        success_rate = 0.7
        if random.random() < success_rate:
            return "accepted"
        else:
            return "rejected"

    def _verify_pcap_docker(self, pcap):
        """Verify PCAP using Docker verifier"""
        try:
            from proofengine.verifier.docker_runner import DockerRunner

            runner = DockerRunner()
            if not runner.build_image():
                print("❌ Failed to build Docker image")
                return "rejected"

            # Create temporary PCAP file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(pcap, f)
                temp_pcap = Path(f.name)

            try:
                result = runner.run_verification([temp_pcap], timeout_s=60)

                if result.get("error"):
                    print(f"❌ Docker verification failed: {result['error']}")
                    return "rejected"

                if result.get("exit_code") == 0:
                    print("✅ Docker verification passed")
                    return "accepted"
                else:
                    print(
                        f"❌ Docker verification failed (exit code: {result['exit_code']})"
                    )
                    return "rejected"

            finally:
                temp_pcap.unlink()

        except Exception as e:
            print(f"❌ Docker verification error: {e}")
            return "rejected"

    def update_state_accepted(self, step, pcap):
        """Update state when step is accepted"""
        # Add artifact to state
        artifact = {
            "id": f"a-{uuid.uuid4().hex[:8]}",
            "type": "pcap",
            "ref_ids": [pcap["id"]],
            "produced_by_journal_id": f"j-{uuid.uuid4().hex[:8]}",
        }

        self.state["A"].append(artifact)

        # Add journal entry
        journal_entry = {
            "id": f"j-{uuid.uuid4().hex[:8]}",
            "ts": datetime.utcnow().isoformat() + "Z",
            "operator": step["operator"],
            "input_refs": step.get("input_refs", []),
            "output_refs": [artifact["id"]],
            "obligations_checked": pcap["obligations"],
            "proofs_attached": [p["id"] for p in pcap["proofs"]],
            "costs": pcap["justification"],
            "prev_entry_hash": self.get_last_journal_hash(),
            "entry_hash": hashlib.sha256(
                f"{step['id']}:{datetime.utcnow()}".encode()
            ).hexdigest(),
        }

        self.state["J"]["entries"].append(journal_entry)

        print(f"✅ Step {step['id']} accepted - artifact {artifact['id']} created")

    def get_last_journal_hash(self):
        """Get hash of last journal entry"""
        entries = self.state["J"].get("entries", [])
        if not entries:
            return "0" * 64
        return entries[-1]["entry_hash"]

    def handle_failure(self, step, pcap):
        """Handle step failure"""
        print(f"❌ Step {step['id']} failed - triggering replan")

        # Create FailReason (for future use)
        # fail_reason = {
        #     "version": "0.1.0",
        #     "code": "test_failure",
        #     "message": f"Step {step['id']} verification failed",
        #     "refs": [step["id"]],
        #     "data": {"step_operator": step["operator"]},
        # }

        # Update metrics
        self.metrics["replans_count"] += 1

        # Simple replan: skip failed step
        print(f"Replanning: skipping step {step['id']}")

    def execute_plan(self):
        """Execute the entire plan"""
        print(f"Executing plan: {self.plan['id']}")
        start_time = datetime.now()

        for step in self.plan["steps"]:
            success = self.execute_step(step)
            if not success:
                print(f"Plan execution failed at step {step['id']}")
                break

        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics["time_ms"] = int(elapsed)

        # Calculate accept rate
        total_steps = len(self.plan["steps"])
        if total_steps > 0:
            self.metrics["accept_rate"] = self.metrics["steps_executed"] / total_steps

        print("\nExecution complete:")
        print(f"  Steps executed: {self.metrics['steps_executed']}/{total_steps}")
        print(f"  Accept rate: {self.metrics['accept_rate']:.1%}")
        print(f"  Replans: {self.metrics['replans_count']}")
        print(f"  Time: {self.metrics['time_ms']}ms")

    def save_updated_state(self):
        """Save updated state"""
        output_path = self.state_path.parent / f"{self.state_path.stem}-updated.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        print(f"Updated state saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Orchestrator skeleton v0.1")
    parser.add_argument("--plan", required=True, help="Plan JSON file")
    parser.add_argument("--state", required=True, help="State JSON file")
    parser.add_argument("--output", help="Output directory for artifacts")

    args = parser.parse_args()

    try:
        orchestrator = Orchestrator(args.plan, args.state)
        orchestrator.load_state()
        orchestrator.execute_plan()
        orchestrator.save_updated_state()

        # Save metrics
        metrics_path = Path(args.output or ".") / "metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(orchestrator.metrics, f, indent=2)
        print(f"Metrics saved to {metrics_path}")

    except Exception as e:
        print(f"Orchestration failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

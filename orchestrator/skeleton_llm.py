#!/usr/bin/env python3
"""
Orchestrator skeleton v0.1 with LLM integration
Plan-Execute-Replan loop with real LLM calls
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

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

    def load_data(self):
        """Load plan and state from files"""
        try:
            with open(self.plan_path, "r") as f:
                self.plan = json.load(f)
            with open(self.state_path, "r") as f:
                self.state = json.load(f)
        except Exception as e:
            raise OrchestratorError(f"Failed to load data: {e}")

    def run(self):
        """Main execution loop"""
        print("🚀 Starting Orchestrator with LLM integration")
        print(f"Plan: {self.plan_path}")
        print(f"State: {self.state_path}")

        start_time = datetime.utcnow()

        # Test LLM connectivity
        print("\n🔍 Testing LLM connectivity...")
        ping_result = self.llm_adapter.ping()
        if ping_result.get("ok"):
            print(f"✅ LLM connected: {ping_result.get('model', 'unknown')}")
        else:
            print(f"⚠️ LLM offline: {ping_result.get('error', 'unknown')}")

        # Execute plan steps
        print(f"\n📋 Executing plan with {len(self.plan.get('steps', []))} steps")

        for i, step in enumerate(self.plan.get("steps", [])):
            print(f"\n--- Step {i+1}: {step.get('operator', 'unknown')} ---")
            success = self.execute_step(step)

            if not success:
                print(f"❌ Step {i+1} failed, triggering replan...")
                self.replan()
                break
            else:
                print(f"✅ Step {i+1} completed successfully")

        # Calculate final metrics
        end_time = datetime.utcnow()
        self.metrics["time_ms"] = int((end_time - start_time).total_seconds() * 1000)

        total_steps = len(self.plan.get("steps", []))
        if total_steps > 0:
            self.metrics["accept_rate"] = self.metrics["steps_executed"] / total_steps

        print("\n📊 Final metrics:")
        print(f"  Accept rate: {self.metrics['accept_rate']:.1%}")
        print(f"  Steps executed: {self.metrics['steps_executed']}")
        print(f"  Replans: {self.metrics['replans_count']}")
        print(f"  Time: {self.metrics['time_ms']}ms")

    def execute_step(self, step):
        """Execute a single step using LLM"""
        print(f"  Executing: {step.get('operator', 'unknown')}")

        # Use LLM to generate action
        try:
            result = self.llm_adapter.call_generalize(
                task=f"Generate action for {step.get('operator', 'unknown')}",
                context={
                    "step": step,
                    "state": self.state,
                    "obligations": self.state.get("K", []),
                },
                constraints=[
                    "JSON output only",
                    "Action must be executable",
                    "Consider all obligations",
                ],
            )

            action = result["response"]
            print(
                f"    Generated action: {action.get('action', {}).get('name', 'unknown')}"
            )

            # Mock verification - in real implementation, this would:
            # 1. Apply action to state
            # 2. Run deterministic verifier
            # 3. Check against obligations

            import random

            success = random.random() > 0.2  # 80% success rate for demo

            if success:
                print("    ✅ Success")
                self.metrics["steps_executed"] += 1
                return True
            else:
                print("    ❌ Verification failed")
                return False

        except Exception as e:
            print(f"    ❌ LLM Error: {e}")
            return False

    def replan(self):
        """Trigger replanning using LLM"""
        print("🔄 Replanning...")

        try:
            result = self.llm_adapter.call_meet(
                task="Replan after failure",
                x_summary=self.state,
                obligations=self.state.get("K", []),
            )

            new_plan = result["response"]
            print(f"    New plan: {new_plan.get('plan', [])}")

            # Update plan with new steps
            if "plan" in new_plan:
                self.plan["steps"] = [
                    {"operator": step, "params": {}} for step in new_plan["plan"]
                ]

            self.metrics["replans_count"] += 1

        except Exception as e:
            print(f"    ❌ Replan failed: {e}")
            # Fallback to original plan
            pass


def main():
    parser = argparse.ArgumentParser(description="Orchestrator with LLM integration")
    parser.add_argument("--plan", required=True, help="Path to plan JSON file")
    parser.add_argument("--state", required=True, help="Path to state JSON file")
    parser.add_argument(
        "--llm", choices=["kimi", "mock"], default="kimi", help="LLM to use"
    )
    parser.add_argument(
        "--verifier", choices=["local", "docker"], default="local", help="Verifier mode"
    )

    args = parser.parse_args()

    # Create LLM adapter based on choice
    if args.llm == "mock":
        from unittest.mock import MagicMock

        mock_adapter = MagicMock()
        mock_adapter.ping.return_value = {"ok": True, "model": "mock"}
        mock_adapter.call_generalize.return_value = {
            "response": {"action": {"name": "mock_action"}},
            "meta": {"cache_hit": False},
        }
        mock_adapter.call_meet.return_value = {
            "response": {"plan": ["mock_step1", "mock_step2"]},
            "meta": {"cache_hit": False},
        }
        llm_adapter = mock_adapter
    else:
        llm_adapter = OrchestratorLLMAdapter()

    try:
        orchestrator = Orchestrator(args.plan, args.state, llm_adapter, args.verifier)
        orchestrator.run()
    except OrchestratorError as e:
        print(f"❌ Orchestrator error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

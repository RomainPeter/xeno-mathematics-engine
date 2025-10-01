"""
Hermetic runner stub for Discovery Engine 2-Cat.
Records environment, seeds, prompt_hash, and costs for reproducibility.
"""

import os
import json
import hashlib
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class HermeticRecord:
    """Record of hermetic execution."""

    id: str
    timestamp: str
    environment: Dict[str, str]
    seeds: Dict[str, Any]
    prompt_hash: str
    costs: Dict[str, float]
    inputs: List[str]
    outputs: List[str]
    merkle_hash: str
    signature: Optional[str] = None


class HermeticRunner:
    """Hermetic runner for reproducible execution."""

    def __init__(self, work_dir: str = "out/hermetic"):
        self.work_dir = work_dir
        self.records: List[HermeticRecord] = []
        os.makedirs(work_dir, exist_ok=True)

    def record_execution(
        self,
        environment: Dict[str, str],
        seeds: Dict[str, Any],
        prompt_hash: str,
        costs: Dict[str, float],
        inputs: List[str],
        outputs: List[str],
    ) -> HermeticRecord:
        """Record a hermetic execution."""

        # Generate unique ID
        exec_id = f"hermetic_{len(self.records)}_{int(datetime.now().timestamp())}"

        # Create record
        record = HermeticRecord(
            id=exec_id,
            timestamp=datetime.now().isoformat(),
            environment=environment,
            seeds=seeds,
            prompt_hash=prompt_hash,
            costs=costs,
            inputs=inputs,
            outputs=outputs,
            merkle_hash="",  # Will be calculated
            signature=None,
        )

        # Calculate Merkle hash
        record.merkle_hash = self._calculate_merkle_hash(record)

        # Store record
        self.records.append(record)

        # Write to file
        self._write_record(record)

        return record

    def _calculate_merkle_hash(self, record: HermeticRecord) -> str:
        """Calculate Merkle hash for the record."""
        # Create hashable data
        hash_data = {
            "id": record.id,
            "timestamp": record.timestamp,
            "environment": record.environment,
            "seeds": record.seeds,
            "prompt_hash": record.prompt_hash,
            "costs": record.costs,
            "inputs": record.inputs,
            "outputs": record.outputs,
        }

        # Calculate hash
        return hashlib.sha256(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()

    def _write_record(self, record: HermeticRecord):
        """Write record to file."""
        record_file = os.path.join(self.work_dir, f"{record.id}.json")

        with open(record_file, "w") as f:
            json.dump(asdict(record), f, indent=2)

    def get_merkle_root(self) -> str:
        """Get Merkle root of all records."""
        if not self.records:
            return "0" * 64

        # Combine all record hashes
        hashes = [record.merkle_hash for record in self.records]
        combined = "".join(hashes)

        return hashlib.sha256(combined.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify integrity of all records."""
        for record in self.records:
            # Recalculate hash
            expected_hash = self._calculate_merkle_hash(record)
            if record.merkle_hash != expected_hash:
                return False
        return True

    def export_journal(self) -> Dict[str, Any]:
        """Export journal in Discovery Engine format."""
        return {
            "version": "0.1.0",
            "type": "hermetic_journal",
            "merkle_root": self.get_merkle_root(),
            "records": [asdict(record) for record in self.records],
            "integrity_verified": self.verify_integrity(),
            "export_timestamp": datetime.now().isoformat(),
        }


def run_hermetic_command(
    command: List[str],
    environment: Dict[str, str],
    seeds: Dict[str, Any],
    prompt_hash: str,
    costs: Dict[str, float],
) -> HermeticRecord:
    """Run a command hermetically and record the execution."""

    runner = HermeticRunner()

    # Capture inputs (command and environment)
    inputs = [
        f"command: {' '.join(command)}",
        f"environment: {json.dumps(environment)}",
        f"seeds: {json.dumps(seeds)}",
        f"prompt_hash: {prompt_hash}",
    ]

    # Run command
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env={**os.environ, **environment},
            timeout=300,  # 5 minutes timeout
        )

        # Capture outputs
        outputs = [
            f"stdout: {result.stdout}",
            f"stderr: {result.stderr}",
            f"returncode: {result.returncode}",
        ]

        # Record execution
        record = runner.record_execution(
            environment=environment,
            seeds=seeds,
            prompt_hash=prompt_hash,
            costs=costs,
            inputs=inputs,
            outputs=outputs,
        )

        return record

    except subprocess.TimeoutExpired:
        # Handle timeout
        outputs = ["timeout: command exceeded 5 minutes"]
        record = runner.record_execution(
            environment=environment,
            seeds=seeds,
            prompt_hash=prompt_hash,
            costs=costs,
            inputs=inputs,
            outputs=outputs,
        )
        return record

    except Exception as e:
        # Handle other errors
        outputs = [f"error: {str(e)}"]
        record = runner.record_execution(
            environment=environment,
            seeds=seeds,
            prompt_hash=prompt_hash,
            costs=costs,
            inputs=inputs,
            outputs=outputs,
        )
        return record


if __name__ == "__main__":
    # Test hermetic runner
    print("Testing Hermetic Runner...")

    # Create test environment
    test_env = {
        "DISCOVERY_ENGINE_VERSION": "0.1.0",
        "PYTHONPATH": ".",
        "TEST_MODE": "true",
    }

    test_seeds = {"random_seed": 42, "llm_seed": "test_prompt_hash_123"}

    test_costs = {
        "time_ms": 100,
        "audit_cost": 10,
        "legal_risk": 0.1,
        "tech_debt": 0.05,
    }

    # Run test command
    record = run_hermetic_command(
        command=["python", "-c", "print('Hello from hermetic runner!')"],
        environment=test_env,
        seeds=test_seeds,
        prompt_hash="test_prompt_hash_123",
        costs=test_costs,
    )

    print(f"✅ Hermetic execution recorded: {record.id}")
    print(f"✅ Merkle hash: {record.merkle_hash[:16]}...")
    print(
        f"✅ Integrity verified: {record.merkle_hash == hashlib.sha256(json.dumps({"
        f"'id': record.id, "
        f"'timestamp': record.timestamp, "
        f"'environment': record.environment, "
        f"'seeds': record.seeds, "
        f"'prompt_hash': record.prompt_hash, "
        f"'costs': record.costs, "
        f"'inputs': record.inputs, "
        f"'outputs': record.outputs"
        f"}, sort_keys=True).encode()).hexdigest()}"
    )

    print("✅ Hermetic runner test completed!")

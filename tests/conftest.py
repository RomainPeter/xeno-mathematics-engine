#!/usr/bin/env python3
"""
Pytest configuration and fixtures for PEFC tests.
"""
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Generator
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from pefc.pack.merkle import PackEntry, build_entries


@pytest.fixture
def cli_runner() -> CliRunner:
    """CLI runner for testing Typer commands."""
    return CliRunner()


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Temporary workspace for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for tests."""
    return {
        "pack": {
            "version": "v0.1.0",
            "pack_name": "test-pack",
            "out_dir": "dist",
            "zip_name": "{pack_name}-{version}.zip",
            "include_manifest": True,
            "include_merkle": True,
        },
        "logging": {
            "level": "DEBUG",
            "json_mode": True,
            "gha_annotations": False,
        },
        "metrics": {
            "sources": ["bench/metrics/**/*.json"],
            "include_aggregates": False,
            "weight_key": "n_items",
            "dedup": "first",
            "backend": "auto",
            "reduce_policy": "intersect",
            "bounded_metrics": ["coverage_gain", "novelty_avg"],
            "schema_path": "schema/summary.schema.json",
        },
        "merkle": {
            "chunk_size": 65536,
            "algorithm": "sha256",
        },
        "sign": {
            "enabled": False,
            "provider": "cosign",
            "key_ref": None,
            "required": False,
        },
        "docs": {
            "onepager": {
                "template_path": None,
                "output_file": "ONEPAGER.md",
            }
        },
        "sbom": {"path": None},
        "capabilities": {
            "allowlist": [],
            "denylist": [],
            "registry": [
                {
                    "id": "hs-tree",
                    "module": "pefc.capabilities.handlers.hstree:HSTreeHandler",
                    "enabled": True,
                    "params": {},
                }
            ],
        },
        "pipelines": {
            "default": "test_pack",
            "defs": {
                "test_pack": {
                    "name": "Test Pack",
                    "steps": [
                        {"type": "CollectSeeds", "name": "CollectSeeds", "params": {}},
                        {
                            "type": "ComputeMerkle",
                            "name": "ComputeMerkle",
                            "params": {},
                        },
                        {"type": "RenderDocs", "name": "RenderDocs", "params": {}},
                        {"type": "PackZip", "name": "PackZip", "params": {}},
                        {"type": "SignArtifact", "name": "SignArtifact", "params": {}},
                    ],
                }
            },
        },
        "profiles": {
            "dev": {
                "logging": {"level": "DEBUG", "json_mode": True},
                "sign": {"enabled": False},
            }
        },
    }


@pytest.fixture
def sample_metrics_data() -> List[Dict[str, Any]]:
    """Sample metrics data for testing."""
    return [
        {
            "run_id": "run_001",
            "timestamp": "2025-01-01T00:00:00Z",
            "metrics": {
                "coverage_gain": 0.75,
                "novelty_avg": 0.85,
                "n_items": 100,
                "execution_time": 1.5,
            },
        },
        {
            "run_id": "run_002",
            "timestamp": "2025-01-01T00:01:00Z",
            "metrics": {
                "coverage_gain": 0.80,
                "novelty_avg": 0.90,
                "n_items": 120,
                "execution_time": 1.8,
            },
        },
        {
            "run_id": "run_003",
            "timestamp": "2025-01-01T00:02:00Z",
            "metrics": {
                "coverage_gain": 0.70,
                "novelty_avg": 0.80,
                "n_items": 90,
                "execution_time": 1.2,
            },
        },
    ]


@pytest.fixture
def sample_files(temp_workspace: Path) -> List[Path]:
    """Create sample files for testing."""
    files = []

    # Create test files
    file1 = temp_workspace / "file1.txt"
    file1.write_text("content1")
    files.append(file1)

    file2 = temp_workspace / "file2.txt"
    file2.write_text("content2")
    files.append(file2)

    # Create metrics file
    metrics_file = temp_workspace / "metrics.json"
    metrics_data = [
        {
            "run_id": "test_001",
            "timestamp": "2025-01-01T00:00:00Z",
            "metrics": {
                "coverage_gain": 0.75,
                "novelty_avg": 0.85,
                "n_items": 100,
            },
        }
    ]
    metrics_file.write_text(json.dumps(metrics_data, indent=2))
    files.append(metrics_file)

    return files


@pytest.fixture
def sample_pack_entries(sample_files: List[Path]) -> List[PackEntry]:
    """Create sample pack entries for testing."""
    entries = []
    for i, file_path in enumerate(sample_files):
        entry = PackEntry(
            arcname=f"file{i+1}.txt",
            src_path=file_path,
            size=file_path.stat().st_size,
            sha256="",  # Will be computed
            leaf="",  # Will be computed
        )
        entries.append(entry)

    # Compute hashes
    entries = build_entries([(e.src_path, e.arcname) for e in entries])
    return entries


@pytest.fixture
def mock_cosign():
    """Mock cosign for testing."""
    mock = Mock()
    mock.sign_blob.return_value = "mock_signature"
    mock.verify_blob.return_value = True
    return mock


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing."""
    bus = Mock()
    bus.subscribe = Mock()
    bus.publish = Mock()
    return bus


@pytest.fixture
def memory_log_sink():
    """Memory log sink for capturing events."""

    class MemorySink:
        def __init__(self):
            self.events = []

        def handler(self, event_type: str, data: Dict[str, Any]):
            self.events.append({"type": event_type, "data": data})

        def clear(self):
            self.events.clear()

    return MemorySink()


def sha256_stream(file_path: Path) -> str:
    """Compute SHA256 of a file stream."""
    import hashlib

    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def sha256_helper():
    """Helper for computing SHA256 hashes."""
    return sha256_stream


def create_minimal_pipeline_config() -> Dict[str, Any]:
    """Create minimal pipeline configuration for testing."""
    return {
        "name": "Test Pipeline",
        "steps": [
            {
                "type": "CollectSeeds",
                "name": "CollectSeeds",
                "params": {"sources": ["test/metrics/**/*.json"]},
            },
            {
                "type": "ComputeMerkle",
                "name": "ComputeMerkle",
                "params": {},
            },
            {
                "type": "PackZip",
                "name": "PackZip",
                "params": {"include_manifest": True, "include_merkle": True},
            },
        ],
    }


@pytest.fixture
def minimal_pipeline_config():
    """Minimal pipeline configuration for testing."""
    return create_minimal_pipeline_config()


def generate_test_runs(count: int = 10) -> List[Dict[str, Any]]:
    """Generate test runs data for testing."""
    import random
    from datetime import datetime, timedelta

    runs = []
    base_time = datetime(2025, 1, 1, 0, 0, 0)

    for i in range(count):
        run = {
            "run_id": f"test_run_{i:03d}",
            "timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
            "metrics": {
                "coverage_gain": round(random.uniform(0.5, 1.0), 3),
                "novelty_avg": round(random.uniform(0.6, 1.0), 3),
                "n_items": random.randint(50, 200),
                "execution_time": round(random.uniform(0.5, 3.0), 2),
            },
        }
        runs.append(run)

    return runs


@pytest.fixture
def test_runs():
    """Generate test runs for testing."""
    return generate_test_runs(10)


@pytest.fixture
def large_test_runs():
    """Generate large test runs for performance testing."""
    return generate_test_runs(1000)

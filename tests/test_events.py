"""
Tests for the event bus and structured telemetry system.
Tests EventBus, sinks, manifest, and PCAP functionality.
"""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from pefc.events import (AuditManifest, EventBus, EventBusConfig, EventLevel,
                         EventType, FileJSONLSink, MemorySink, MerkleTree,
                         PCAPManager, PCAPSchema, PCAPWriter, RotatingFileSink,
                         StdoutJSONLSink, create_event, create_incident_event,
                         create_orchestrator_start_event, replay_journal)


class TestEventBus:
    """Test EventBus functionality."""

    @pytest.fixture
    def event_bus(self):
        """Create a test event bus."""
        config = EventBusConfig(buffer_size=100, sinks=["memory"], drop_oldest=True)
        return EventBus(config)

    @pytest.mark.asyncio
    async def test_event_bus_start_stop(self, event_bus):
        """Test event bus start/stop."""
        await event_bus.start()
        assert event_bus.drain_task is not None
        assert not event_bus.drain_task.done()

        await event_bus.stop()
        assert event_bus.drain_task.cancelled()

    @pytest.mark.asyncio
    async def test_publish_event(self, event_bus):
        """Test publishing events."""
        await event_bus.start()

        # Create test event
        event = create_event(
            EventType.ORCHESTRATOR_START,
            {"test": "data"},
            trace_id="test-trace",
            run_id="test-run",
        )

        # Publish event
        await event_bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        # Check stats
        stats = event_bus.get_stats()
        assert stats["published"] >= 1

        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_concurrent_publish(self, event_bus):
        """Test concurrent event publishing."""
        await event_bus.start()

        # Publish 1000 events concurrently
        events = []
        for i in range(1000):
            event = create_event(
                EventType.AE_STEP, {"step": i}, trace_id="test-trace", run_id="test-run"
            )
            events.append(event)

        # Publish all events
        await asyncio.gather(*[event_bus.publish(event) for event in events])

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check stats
        stats = event_bus.get_stats()
        assert stats["published"] >= 1000

        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_backpressure_handling(self, event_bus):
        """Test backpressure handling with small buffer."""
        # Recreate bus with small deque buffer and publish before starting drain
        small_bus = EventBus(EventBusConfig(buffer_size=5, sinks=["memory"], drop_oldest=True))

        # Publish more events than buffer can hold
        events = []
        for i in range(20):
            event = create_event(
                EventType.AE_STEP, {"step": i}, trace_id="test-trace", run_id="test-run"
            )
            events.append(event)

        # Publish all events
        await asyncio.gather(*[small_bus.publish(event) for event in events])

        # Now start the bus to drain what remains
        await small_bus.start()

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check stats
        stats = small_bus.get_stats()
        assert stats["published"] >= 20
        assert stats["dropped"] >= 1  # Drop-oldest should trigger

        await small_bus.stop()

    @pytest.mark.asyncio
    async def test_replay_journal_file(self):
        """Write events to a JSONL file and replay them with replay_journal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            events_file = Path(temp_dir) / "events.jsonl"
            bus = EventBus(
                EventBusConfig(buffer_size=32, sinks=["file"], file_path=str(events_file))
            )

            await bus.start()
            e1 = create_orchestrator_start_event(run_id="r", trace_id="t", payload={"x": 1})
            e2 = create_incident_event(
                run_id="r",
                trace_id="t",
                step_id="s",
                code="err",
                message="m",
                detail={},
            )
            await bus.publish(e1)
            await bus.publish(e2)
            await asyncio.sleep(0.2)
            await bus.flush()
            await bus.stop()

            assert events_file.exists()

            seen = []

            def cb(ev):
                seen.append(ev.type)

            n = replay_journal(events_file, cb)
            assert n >= 2
            assert "Orchestrator.Start" in seen or "Orchestrator.Start" in [
                getattr(t, "value", t) for t in seen
            ]

    @pytest.mark.asyncio
    async def test_subscriber_callback(self, event_bus):
        """Test subscriber callback functionality."""
        received_events = []

        def callback(event):
            received_events.append(event)

        event_bus.subscribe(callback)
        await event_bus.start()

        # Publish test event
        event = create_event(
            EventType.ORCHESTRATOR_START,
            {"test": "data"},
            trace_id="test-trace",
            run_id="test-run",
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.1)

        # Check callback was called
        assert len(received_events) >= 1
        assert received_events[0].type == EventType.ORCHESTRATOR_START

        await event_bus.stop()

    @pytest.mark.asyncio
    async def test_async_subscriber_callback(self, event_bus):
        """Test async subscriber callback functionality."""
        received_events = []

        async def async_callback(event):
            received_events.append(event)

        event_bus.subscribe(async_callback)
        await event_bus.start()

        # Publish test event
        event = create_event(
            EventType.ORCHESTRATOR_START,
            {"test": "data"},
            trace_id="test-trace",
            run_id="test-run",
        )

        await event_bus.publish(event)
        await asyncio.sleep(0.1)

        # Check callback was called
        assert len(received_events) >= 1
        assert received_events[0].type == EventType.ORCHESTRATOR_START

        await event_bus.stop()


class TestEventSinks:
    """Test event sink functionality."""

    def test_stdout_sink(self):
        """Test stdout sink."""
        sink = StdoutJSONLSink()

        # Test write
        event_dict = {"type": "test", "data": "value"}
        sink.write(event_dict)

        # Check stats
        stats = sink.get_stats()
        assert stats["written"] >= 1

    def test_memory_sink(self):
        """Test memory sink."""
        sink = MemorySink()

        # Test write
        event_dict = {"type": "test", "data": "value"}
        sink.write(event_dict)

        # Check stats
        stats = sink.get_stats()
        assert stats["written"] == 1
        assert stats["stored"] == 1

        # Check events
        events = sink.get_events()
        assert len(events) == 1
        assert events[0]["type"] == "test"

        # Test filtering
        sink.write({"type": "other", "data": "value2"})
        test_events = sink.get_events_by_type("test")
        assert len(test_events) == 1

        # Test clear
        sink.clear()
        assert len(sink.get_events()) == 0

    def test_file_sink(self):
        """Test file sink."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.jsonl"
            sink = FileJSONLSink(str(file_path))

            # Test write
            event_dict = {"type": "test", "data": "value"}
            sink.write(event_dict)
            sink.flush()

            # Check file exists and has content
            assert file_path.exists()
            with open(file_path, "r") as f:
                content = f.read()
                assert "test" in content

            # Check stats
            stats = sink.get_stats()
            assert stats["written"] >= 1

    def test_rotating_file_sink(self):
        """Test rotating file sink."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "test.jsonl"
            sink = RotatingFileSink(str(base_path), max_size_mb=1)

            # Test write
            event_dict = {"type": "test", "data": "value"}
            sink.write(event_dict)
            sink.flush()

            # Check file exists
            assert base_path.exists()

            # Check stats
            stats = sink.get_stats()
            assert stats["written"] >= 1


class TestAuditManifest:
    """Test audit manifest functionality."""

    def test_manifest_creation(self):
        """Test manifest creation."""
        manifest = AuditManifest(run_id="test-run")

        # Add files
        manifest.add_file("test1.json", "hash1", 100)
        manifest.add_file("test2.json", "hash2", 200)

        # Check manifest
        assert manifest.run_id == "test-run"
        assert len(manifest.files) == 2
        assert manifest.total_bytes == 300

        # Check file info
        file_info = manifest.get_file_info("test1.json")
        assert file_info is not None
        assert file_info.sha256 == "hash1"
        assert file_info.bytes == 100

    def test_merkle_root_calculation(self):
        """Test Merkle root calculation."""
        manifest = AuditManifest(run_id="test-run")

        # Add files
        manifest.add_file("test1.json", "hash1", 100)
        manifest.add_file("test2.json", "hash2", 200)

        # Calculate Merkle root
        root = manifest.calculate_merkle_root()
        assert root != ""
        assert manifest.merkle_root == root

    def test_manifest_serialization(self):
        """Test manifest serialization."""
        manifest = AuditManifest(run_id="test-run")
        manifest.add_file("test1.json", "hash1", 100)
        manifest.calculate_merkle_root()

        # Test to_dict
        data = manifest.to_dict()
        assert data["run_id"] == "test-run"
        assert len(data["files"]) == 1

        # Test to_json
        json_str = manifest.to_json()
        assert "test-run" in json_str

        # Test from_dict
        new_manifest = AuditManifest.from_dict(data)
        assert new_manifest.run_id == "test-run"
        assert len(new_manifest.files) == 1

    def test_manifest_integrity_verification(self):
        """Test manifest integrity verification."""
        manifest = AuditManifest(run_id="test-run")
        manifest.add_file("test1.json", "hash1", 100)
        manifest.calculate_merkle_root()

        # Verify integrity
        assert manifest.verify_integrity()

        # Tamper with manifest
        manifest.merkle_root = "tampered"
        assert not manifest.verify_integrity()


class TestMerkleTree:
    """Test Merkle tree functionality."""

    def test_merkle_tree_creation(self):
        """Test Merkle tree creation."""
        data = ["item1", "item2", "item3", "item4"]
        tree = MerkleTree(data)

        # Check tree properties
        assert tree.get_leaf_count() == 4
        assert tree.get_root() != ""
        assert tree.get_tree_height() > 0

    def test_merkle_proof(self):
        """Test Merkle proof generation and verification."""
        data = ["item1", "item2", "item3", "item4"]
        tree = MerkleTree(data)

        # Get proof for index 0
        proof = tree.get_proof(0)
        assert len(proof) > 0

        # Verify proof
        leaf_hash = tree.tree[0]  # First leaf
        assert tree.verify_proof(0, proof, leaf_hash)

        # Test with wrong hash
        wrong_hash = "wrong"
        assert not tree.verify_proof(0, proof, wrong_hash)

    def test_merkle_tree_single_item(self):
        """Test Merkle tree with single item."""
        data = ["single"]
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 1
        assert tree.get_root() != ""
        assert tree.get_tree_height() == 0

    def test_merkle_tree_empty(self):
        """Test Merkle tree with empty data."""
        data = []
        tree = MerkleTree(data)

        assert tree.get_leaf_count() == 0
        assert tree.get_root() == ""
        assert tree.get_tree_height() == 0


class TestPCAP:
    """Test PCAP functionality."""

    def test_pcap_creation(self):
        """Test PCAP creation."""
        pcap = PCAPSchema(
            action="test_action",
            context_hash="test_hash",
            obligations=["obligation1", "obligation2"],
            proofs=[{"type": "proof1", "data": "value1"}],
            justification={"reason": "test"},
        )

        # Calculate hash
        hash_value = pcap.calculate_hash()
        assert hash_value != ""
        assert pcap.sha256 == hash_value

        # Check properties
        assert pcap.get_obligation_count() == 2
        assert pcap.get_proof_count() == 1

    def test_pcap_serialization(self):
        """Test PCAP serialization."""
        pcap = PCAPSchema(
            action="test_action",
            context_hash="test_hash",
            obligations=["obligation1"],
            proofs=[{"type": "proof1"}],
            justification={"reason": "test"},
        )
        pcap.calculate_hash()

        # Test to_dict
        data = pcap.to_dict()
        assert data["action"] == "test_action"
        assert data["sha256"] == pcap.sha256

        # Test to_json
        json_str = pcap.to_json()
        assert "test_action" in json_str

        # Test from_dict
        new_pcap = PCAPSchema.from_dict(data)
        assert new_pcap.action == "test_action"
        assert new_pcap.sha256 == pcap.sha256

    def test_pcap_integrity_verification(self):
        """Test PCAP integrity verification."""
        pcap = PCAPSchema(
            action="test_action",
            context_hash="test_hash",
            obligations=["obligation1"],
            proofs=[{"type": "proof1"}],
            justification={"reason": "test"},
        )
        pcap.calculate_hash()

        # Verify integrity
        assert pcap.verify_integrity()

        # Tamper with PCAP
        pcap.sha256 = "tampered"
        assert not pcap.verify_integrity()

    def test_pcap_writer(self):
        """Test PCAP writer."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = PCAPWriter(temp_dir)

            # Create PCAP
            pcap = PCAPSchema(
                action="test_action",
                context_hash="test_hash",
                obligations=["obligation1"],
                proofs=[{"type": "proof1"}],
                justification={"reason": "test"},
            )
            pcap.calculate_hash()

            # Write PCAP
            file_path = writer.write_pcap(pcap, "step1", "action1")
            assert Path(file_path).exists()

            # Check stats
            stats = writer.get_stats()
            assert stats["written"] >= 1

            # List PCAPs
            pcaps = writer.list_pcaps()
            assert len(pcaps) >= 1

    def test_pcap_manager(self):
        """Test PCAP manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PCAPManager(temp_dir)

            # Create PCAP
            pcap = manager.create_pcap(
                action="test_action",
                context_hash="test_hash",
                step_id="step1",
                obligations=["obligation1"],
                proofs=[{"type": "proof1"}],
                justification={"reason": "test"},
            )

            # Check PCAP
            assert pcap.action == "test_action"
            assert pcap.sha256 != ""

            # Write PCAP
            file_path = manager.write_pcap(pcap, "step1", "action1")
            assert Path(file_path).exists()

            # Check stats
            stats = manager.get_stats()
            assert stats["total_pcaps"] >= 1


class TestEventTypes:
    """Test event type creation."""

    def test_create_event(self):
        """Test basic event creation."""
        event = create_event(
            EventType.ORCHESTRATOR_START,
            {"test": "data"},
            trace_id="test-trace",
            run_id="test-run",
        )

        assert event.type == EventType.ORCHESTRATOR_START
        assert event.trace_id == "test-trace"
        assert event.run_id == "test-run"
        assert event.payload["test"] == "data"

    def test_create_orchestrator_start_event(self):
        """Test orchestrator start event creation."""
        event = create_orchestrator_start_event(
            run_id="test-run", trace_id="test-trace", payload={"test": "data"}
        )

        assert event.type == EventType.ORCHESTRATOR_START
        assert event.phase == "Orchestrator"
        assert event.level == EventLevel.INFO

    def test_create_incident_event(self):
        """Test incident event creation."""
        event = create_incident_event(
            run_id="test-run",
            trace_id="test-trace",
            step_id="test-step",
            code="test_error",
            message="Test error message",
            detail={"error": "details"},
        )

        assert event.type == EventType.INCIDENT
        assert event.phase == "Incident"
        assert event.level == EventLevel.ERROR
        assert event.payload["code"] == "test_error"
        assert event.payload["message"] == "Test error message"


class TestEventIntegration:
    """Test event system integration."""

    @pytest.mark.asyncio
    async def test_full_event_flow(self):
        """Test complete event flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create event bus with file sink
            config = EventBusConfig(
                buffer_size=100,
                sinks=["file"],
                file_path=str(Path(temp_dir) / "events.jsonl"),
            )
            event_bus = EventBus(config)

            # Start event bus
            await event_bus.start()

            # Publish various events
            events = [
                create_orchestrator_start_event(
                    run_id="test-run", trace_id="test-trace", payload={"test": "data"}
                ),
                create_incident_event(
                    run_id="test-run",
                    trace_id="test-trace",
                    step_id="test-step",
                    code="test_error",
                    message="Test error",
                    detail={},
                ),
            ]

            for event in events:
                await event_bus.publish(event)

            # Wait for processing
            await asyncio.sleep(0.5)

            # Check file was created
            events_file = Path(temp_dir) / "events.jsonl"
            assert events_file.exists()

            # Check file content
            with open(events_file, "r") as f:
                lines = f.readlines()
                assert len(lines) >= 2

                # Parse first event
                first_event = json.loads(lines[0])
                assert first_event["type"] == "Orchestrator.Start"
                assert first_event["run_id"] == "test-run"

            # Stop event bus
            await event_bus.stop()

    @pytest.mark.asyncio
    async def test_event_sequence_numbers(self):
        """Test event sequence numbers are monotonic."""
        event_bus = EventBus(EventBusConfig(sinks=["memory"]))
        await event_bus.start()

        # Publish multiple events
        for i in range(10):
            event = create_event(
                EventType.AE_STEP, {"step": i}, trace_id="test-trace", run_id="test-run"
            )
            await event_bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check sequence numbers
        memory_sink = event_bus.sinks[0]
        events = memory_sink.get_events()

        # Check sequence numbers are monotonic
        seq_numbers = [event["seq"] for event in events]
        assert seq_numbers == sorted(seq_numbers)

        await event_bus.stop()

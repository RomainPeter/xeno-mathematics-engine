"""
Demonstration script for the event bus and structured telemetry system.
Shows EventBus, sinks, manifest, and PCAP functionality.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from pefc.events import (
    EventBus,
    EventBusConfig,
    EventType,
    AuditManifest,
    MerkleTree,
    PCAPManager,
    create_event,
    create_orchestrator_start_event,
    create_ae_step_event,
    create_cegis_iter_start_event,
    create_verify_attempt_event,
)


async def demo_basic_event_bus():
    """Demonstrate basic EventBus functionality."""
    print("=== Basic EventBus Demo ===")

    # Create event bus with memory sink
    config = EventBusConfig(buffer_size=100, sinks=["memory"], drop_oldest=True)
    event_bus = EventBus(config)

    # Start event bus
    await event_bus.start()
    print("EventBus started")

    # Publish some events
    events = [
        create_orchestrator_start_event(
            run_id="demo-run", trace_id="demo-trace", payload={"demo": "data"}
        ),
        create_ae_step_event(
            run_id="demo-run",
            trace_id="demo-trace",
            step_id="step1",
            payload={"concept": "test_concept"},
        ),
        create_cegis_iter_start_event(
            run_id="demo-run",
            trace_id="demo-trace",
            step_id="step2",
            iteration=1,
            payload={"candidate": "test_candidate"},
        ),
        create_verify_attempt_event(
            run_id="demo-run",
            trace_id="demo-trace",
            step_id="step3",
            payload={"verification": "test_verification"},
        ),
    ]

    for event in events:
        await event_bus.publish(event)
        print(f"Published event: {event.type.value}")

    # Wait for processing
    await asyncio.sleep(0.5)

    # Check stats
    stats = event_bus.get_stats()
    print(f"EventBus stats: {stats}")

    # Check memory sink
    memory_sink = event_bus.sinks[0]
    stored_events = memory_sink.get_events()
    print(f"Stored events: {len(stored_events)}")

    # Show event types
    event_types = [event["type"] for event in stored_events]
    print(f"Event types: {event_types}")

    # Stop event bus
    await event_bus.stop()
    print("EventBus stopped")


async def demo_file_sink():
    """Demonstrate file sink functionality."""
    print("\n=== File Sink Demo ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create event bus with file sink
        config = EventBusConfig(
            buffer_size=100,
            sinks=["file"],
            file_path=str(Path(temp_dir) / "demo_events.jsonl"),
        )
        event_bus = EventBus(config)

        # Start event bus
        await event_bus.start()
        print("EventBus with file sink started")

        # Publish events
        for i in range(5):
            event = create_event(
                EventType.AE_STEP,
                {"step": i, "data": f"step_{i}_data"},
                trace_id="demo-trace",
                run_id="demo-run",
            )
            await event_bus.publish(event)
            print(f"Published event {i}")

        # Wait for processing
        await asyncio.sleep(0.5)

        # Check file was created
        events_file = Path(temp_dir) / "demo_events.jsonl"
        if events_file.exists():
            print(f"Events file created: {events_file}")

            # Read and display events
            with open(events_file, "r") as f:
                lines = f.readlines()
                print(f"Events written: {len(lines)}")

                # Show first event
                if lines:
                    first_event = json.loads(lines[0])
                    print(f"First event: {first_event['type']} - {first_event['payload']}")

        # Stop event bus
        await event_bus.stop()

        # Close file sinks
        for sink in event_bus.sinks:
            if hasattr(sink, "close"):
                sink.close()

        print("EventBus stopped")


async def demo_concurrent_events():
    """Demonstrate concurrent event publishing."""
    print("\n=== Concurrent Events Demo ===")

    # Create event bus
    config = EventBusConfig(buffer_size=1000, sinks=["memory"], drop_oldest=True)
    event_bus = EventBus(config)

    # Start event bus
    await event_bus.start()
    print("EventBus started for concurrent demo")

    # Publish 1000 events concurrently
    async def publish_events(start, count):
        events = []
        for i in range(start, start + count):
            event = create_event(
                EventType.AE_STEP,
                {"step": i, "data": f"concurrent_step_{i}"},
                trace_id="demo-trace",
                run_id="demo-run",
            )
            events.append(event)

        # Publish all events
        await asyncio.gather(*[event_bus.publish(event) for event in events])
        return len(events)

    # Publish events in batches
    batch_size = 100
    total_events = 0

    for batch in range(10):
        events_published = await publish_events(batch * batch_size, batch_size)
        total_events += events_published
        print(f"Published batch {batch + 1}: {events_published} events")

    # Wait for processing
    await asyncio.sleep(1.0)

    # Check stats
    stats = event_bus.get_stats()
    print(f"Total events published: {total_events}")
    print(f"EventBus stats: {stats}")

    # Check memory sink
    memory_sink = event_bus.sinks[0]
    stored_events = memory_sink.get_events()
    print(f"Events stored: {len(stored_events)}")

    # Stop event bus
    await event_bus.stop()
    print("EventBus stopped")


def demo_audit_manifest():
    """Demonstrate audit manifest functionality."""
    print("\n=== Audit Manifest Demo ===")

    # Create manifest
    manifest = AuditManifest(run_id="demo-run")
    print(f"Created manifest for run: {manifest.run_id}")

    # Add files
    files = [
        ("journal.jsonl", "hash1", 1000),
        ("incidents.jsonl", "hash2", 500),
        ("metrics.json", "hash3", 200),
        ("pcap/step1-action1.json", "hash4", 300),
        ("pcap/step2-action2.json", "hash5", 400),
    ]

    for file_path, file_hash, file_size in files:
        manifest.add_file(file_path, file_hash, file_size)
        print(f"Added file: {file_path} ({file_size} bytes)")

    # Calculate Merkle root
    merkle_root = manifest.calculate_merkle_root()
    print(f"Merkle root: {merkle_root}")

    # Show manifest info
    print(f"Total files: {manifest.get_total_files()}")
    print(f"Total size: {manifest.get_total_size()} bytes")

    # Verify integrity
    is_valid = manifest.verify_integrity()
    print(f"Manifest integrity: {is_valid}")

    # Serialize manifest
    manifest_json = manifest.to_json()
    print(f"Manifest JSON length: {len(manifest_json)} characters")

    # Deserialize manifest
    new_manifest = AuditManifest.from_json(manifest_json)
    print(f"Deserialized manifest run_id: {new_manifest.run_id}")
    print(f"Deserialized manifest files: {new_manifest.get_total_files()}")


def demo_merkle_tree():
    """Demonstrate Merkle tree functionality."""
    print("\n=== Merkle Tree Demo ===")

    # Create Merkle tree
    data = ["item1", "item2", "item3", "item4", "item5"]
    tree = MerkleTree(data)

    print(f"Created Merkle tree with {tree.get_leaf_count()} leaves")
    print(f"Tree height: {tree.get_tree_height()}")
    print(f"Root hash: {tree.get_root()}")

    # Generate proofs
    for i in range(len(data)):
        proof = tree.get_proof(i)
        print(f"Proof for item {i}: {len(proof)} hashes")

        # Verify proof
        leaf_hash = tree.tree[i]
        is_valid = tree.verify_proof(i, proof, leaf_hash)
        print(f"Proof verification for item {i}: {is_valid}")

    # Test with wrong hash
    wrong_hash = "wrong_hash"
    proof = tree.get_proof(0)
    is_valid = tree.verify_proof(0, proof, wrong_hash)
    print(f"Proof verification with wrong hash: {is_valid}")


def demo_pcap():
    """Demonstrate PCAP functionality."""
    print("\n=== PCAP Demo ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create PCAP manager
        manager = PCAPManager(temp_dir)
        print(f"Created PCAP manager in: {temp_dir}")

        # Create PCAPs
        pcaps = []
        for i in range(3):
            pcap = manager.create_pcap(
                action=f"action_{i}",
                context_hash=f"context_hash_{i}",
                step_id=f"step_{i}",
                obligations=[f"obligation_{i}_1", f"obligation_{i}_2"],
                proofs=[{"type": f"proof_{i}", "data": f"proof_data_{i}"}],
                justification={"reason": f"reason_{i}", "iteration": i},
            )
            pcaps.append(pcap)
            print(f"Created PCAP {i}: {pcap.action} (hash: {pcap.sha256[:16]}...)")

        # Write PCAPs
        for i, pcap in enumerate(pcaps):
            file_path = manager.write_pcap(pcap, f"step_{i}", f"action_{i}")
            print(f"Written PCAP {i} to: {file_path}")

        # Check stats
        stats = manager.get_stats()
        print(f"PCAP manager stats: {stats}")

        # List PCAPs
        all_pcaps = manager.list_pcaps()
        print(f"Total PCAPs: {len(all_pcaps)}")

        # Verify PCAPs
        verification_results = manager.verify_all_pcaps()
        valid_count = sum(1 for valid in verification_results.values() if valid)
        print(f"Valid PCAPs: {valid_count}/{len(verification_results)}")


async def demo_full_integration():
    """Demonstrate full event system integration."""
    print("\n=== Full Integration Demo ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create event bus with file sink
        config = EventBusConfig(
            buffer_size=100,
            sinks=["file"],
            file_path=str(Path(temp_dir) / "integration_events.jsonl"),
        )
        event_bus = EventBus(config)

        # Create PCAP manager
        pcap_manager = PCAPManager(temp_dir, event_bus)

        # Start event bus
        await event_bus.start()
        print("Event system started")

        # Simulate orchestrator run
        run_id = "integration-run"
        trace_id = "integration-trace"

        # Start event
        start_event = create_orchestrator_start_event(
            run_id=run_id, trace_id=trace_id, payload={"demo": "integration"}
        )
        await event_bus.publish(start_event)
        print("Published Orchestrator.Start event")

        # Simulate AE steps
        for i in range(3):
            step_id = f"ae_step_{i}"
            ae_event = create_ae_step_event(
                run_id=run_id,
                trace_id=trace_id,
                step_id=step_id,
                payload={"concept": f"concept_{i}", "extent_size": i * 10},
            )
            await event_bus.publish(ae_event)
            print(f"Published AE.Step event {i}")

        # Simulate CEGIS iterations
        for i in range(2):
            step_id = f"cegis_iter_{i}"
            cegis_event = create_cegis_iter_start_event(
                run_id=run_id,
                trace_id=trace_id,
                step_id=step_id,
                iteration=i,
                payload={"candidate": f"candidate_{i}"},
            )
            await event_bus.publish(cegis_event)
            print(f"Published CEGIS.Iter.Start event {i}")

            # Create PCAP for this iteration
            pcap = pcap_manager.create_pcap(
                action=f"cegis_iteration_{i}",
                context_hash=f"context_{i}",
                step_id=step_id,
                obligations=["verify_candidate", "check_compliance"],
                proofs=[{"type": "candidate_proof", "candidate": f"candidate_{i}"}],
                justification={"iteration": i, "reason": "demo"},
            )

            # Write PCAP
            pcap_path = pcap_manager.write_pcap(pcap, step_id, f"action_{i}")
            print(f"Created PCAP: {pcap_path}")

        # Wait for processing
        await asyncio.sleep(1.0)

        # Check results
        events_file = Path(temp_dir) / "integration_events.jsonl"
        if events_file.exists():
            with open(events_file, "r") as f:
                events = [json.loads(line) for line in f.readlines()]
                print(f"Total events written: {len(events)}")

                # Show event types
                event_types = [event["type"] for event in events]
                print(f"Event types: {event_types}")

        # Check PCAPs
        pcap_files = list(Path(temp_dir).glob("pcap/*.json"))
        print(f"PCAP files created: {len(pcap_files)}")

        # Stop event bus
        await event_bus.stop()
        print("Event system stopped")


async def main():
    """Run all demonstrations."""
    print("Event Bus and Structured Telemetry Demo")
    print("=" * 50)

    # Basic EventBus demo
    await demo_basic_event_bus()

    # File sink demo
    await demo_file_sink()

    # Concurrent events demo
    await demo_concurrent_events()

    # Audit manifest demo
    demo_audit_manifest()

    # Merkle tree demo
    demo_merkle_tree()

    # PCAP demo
    demo_pcap()

    # Full integration demo
    await demo_full_integration()

    print("\n" + "=" * 50)
    print("All demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main())

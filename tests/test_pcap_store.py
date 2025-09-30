import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from xme.pcap.model import PCAPEntry
from xme.pcap.store import PCAPStore


def test_pcap_entry_creation():
    """Test PCAPEntry model creation."""
    timestamp = datetime.now(timezone.utc)
    entry = PCAPEntry(
        action="test_action",
        actor="test_actor",
        obligations={"key": "value"},
        deltas={"metric": 1.5},
        timestamp=timestamp,
        psp_ref="psp_123"
    )
    
    assert entry.action == "test_action"
    assert entry.actor == "test_actor"
    assert entry.obligations == {"key": "value"}
    assert entry.deltas == {"metric": 1.5}
    assert entry.psp_ref == "psp_123"


def test_pcap_store_append():
    """Test PCAPStore append functionality."""
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        store = PCAPStore(temp_path)
        
        # Test appending entries
        entry1 = PCAPEntry(
            action="action1",
            actor="actor1",
            timestamp=datetime.now(timezone.utc)
        )
        entry2 = PCAPEntry(
            action="action2",
            actor="actor2",
            obligations={"test": "value"},
            timestamp=datetime.now(timezone.utc)
        )
        
        store.append(entry1)
        store.append(entry2)
        
        # Verify file was created and has content
        assert temp_path.exists()
        content = temp_path.read_text()
        assert "action1" in content
        assert "action2" in content
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_pcap_store_read_all():
    """Test PCAPStore read_all functionality."""
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        store = PCAPStore(temp_path)
        
        # Append some entries
        entry1 = PCAPEntry(
            action="read_test1",
            actor="test_actor",
            timestamp=datetime.now(timezone.utc)
        )
        entry2 = PCAPEntry(
            action="read_test2",
            actor="test_actor",
            deltas={"score": 0.8},
            timestamp=datetime.now(timezone.utc)
        )
        
        store.append(entry1)
        store.append(entry2)
        
        # Read all entries
        entries = list(store.read_all())
        assert len(entries) == 2
        assert entries[0]["action"] == "read_test1"
        assert entries[1]["action"] == "read_test2"
        assert entries[1]["deltas"]["score"] == 0.8
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_pcap_store_empty():
    """Test PCAPStore with non-existent file."""
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=True) as f:
        temp_path = Path(f.name)
    
    store = PCAPStore(temp_path)
    entries = list(store.read_all())
    assert len(entries) == 0


def test_pcap_store_directory_creation():
    """Test that PCAPStore creates parent directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        deep_path = Path(temp_dir) / "deep" / "nested" / "pcap.jsonl"
        store = PCAPStore(deep_path)
        
        entry = PCAPEntry(
            action="deep_test",
            actor="test_actor",
            timestamp=datetime.now(timezone.utc)
        )
        
        store.append(entry)
        
        # Verify directory was created and file exists
        assert deep_path.exists()
        assert deep_path.parent.exists()
        # The parent directory should be "nested", not a subdirectory of it
        assert deep_path.parent.name == "nested"

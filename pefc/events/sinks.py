"""
Event sinks for structured telemetry.
Implements StdoutJSONLSink, FileJSONLSink, and MemorySink.
"""

import json
import gzip
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import time


class EventSink(ABC):
    """Abstract base class for event sinks."""

    @abstractmethod
    def write(self, event_dict: Dict[str, Any]) -> None:
        """Write an event to the sink."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered data."""
        pass


class StdoutJSONLSink(EventSink):
    """Sink that writes events to stdout in JSONL format."""

    def __init__(self):
        self.written_count = 0

    def write(self, event_dict: Dict[str, Any]) -> None:
        """Write event to stdout."""
        try:
            json_line = json.dumps(event_dict, separators=(",", ":"))
            print(json_line, flush=True)
            self.written_count += 1
        except Exception as e:
            print(f"Error writing to stdout: {e}", file=sys.stderr)

    def flush(self) -> None:
        """No-op for stdout."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get sink statistics."""
        return {"written": self.written_count}


class FileJSONLSink(EventSink):
    """Sink that writes events to a file in JSONL format with rotation."""

    def __init__(
        self,
        file_path: str,
        rotate_mb: Optional[int] = None,
        gzip_compress: bool = False,
    ):
        self.file_path = Path(file_path)
        self.rotate_mb = rotate_mb
        self.gzip_compress = gzip_compress
        self.current_file = None
        self.written_count = 0
        self.rotation_count = 0

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def __del__(self):
        """Close file when sink is destroyed."""
        if self.current_file:
            self.current_file.close()
            self.current_file = None

    def write(self, event_dict: Dict[str, Any]) -> None:
        """Write event to file (append & close to avoid Windows file locks)."""
        try:
            # Rotate based on on-disk size
            if self.rotate_mb and self.file_path.exists():
                try:
                    if self.file_path.stat().st_size > (self.rotate_mb * 1024 * 1024):
                        self._rotate_file()
                except Exception as e:
                    import logging
                    logging.warning(f"Error checking file size for rotation: {e}")

            json_line = json.dumps(event_dict, separators=(",", ":"))
            if self.gzip_compress:
                with gzip.open(self.file_path, "at", encoding="utf-8") as f:
                    f.write(json_line + "\n")
            else:
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(json_line + "\n")

            self.written_count += 1

        except Exception as e:
            print(f"Error writing to file {self.file_path}: {e}", file=sys.stderr)

    def flush(self) -> None:
        """Flush file buffer."""
        if self.current_file:
            self.current_file.flush()
            # On Windows, ensure buffers are flushed to disk promptly
            if hasattr(self.current_file, "flush"):
                try:
                    self.current_file.flush()
                except Exception as e:
                    import logging
                    logging.warning(f"Error flushing file: {e}")

    def _should_rotate(self) -> bool:
        """Check if file should be rotated (not used with append strategy)."""
        if not self.rotate_mb or not self.file_path.exists():
            return False
        try:
            return self.file_path.stat().st_size > (self.rotate_mb * 1024 * 1024)
        except Exception as e:
            import logging
            logging.warning(f"Error checking file size: {e}")
            return False

    def _rotate_file(self) -> None:
        """Rotate the current file."""
        if self.current_file:
            self.current_file.close()
            self.current_file = None

        # Rename current file if it exists
        if self.file_path.exists():
            timestamp = int(time.time())
            rotated_path = self.file_path.with_suffix(f".{timestamp}.jsonl")
            if self.gzip_compress:
                rotated_path = rotated_path.with_suffix(".jsonl.gz")

            self.file_path.rename(rotated_path)
            self.rotation_count += 1

    def _open_file(self) -> None:
        """No persistent handle needed (kept for API compatibility)."""
        self.current_file = None

    def close(self):
        """Close the file."""
        if self.current_file:
            self.current_file.close()
            self.current_file = None

    def get_stats(self) -> Dict[str, Any]:
        """Get sink statistics."""
        return {
            "written": self.written_count,
            "rotations": self.rotation_count,
            "file_path": str(self.file_path),
        }


class MemorySink(EventSink):
    """Sink that stores events in memory for testing."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.written_count = 0

    def write(self, event_dict: Dict[str, Any]) -> None:
        """Store event in memory."""
        self.events.append(event_dict)
        self.written_count += 1

    def flush(self) -> None:
        """No-op for memory sink."""
        pass

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all stored events."""
        return self.events.copy()

    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get events filtered by type."""
        return [e for e in self.events if e.get("type") == event_type]

    def get_events_by_phase(self, phase: str) -> List[Dict[str, Any]]:
        """Get events filtered by phase."""
        return [e for e in self.events if e.get("phase") == phase]

    def clear(self) -> None:
        """Clear all stored events."""
        self.events.clear()
        self.written_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get sink statistics."""
        return {
            "written": self.written_count,
            "stored": len(self.events),
        }


class RotatingFileSink(EventSink):
    """Sink that rotates files based on time or size."""

    def __init__(
        self,
        base_path: str,
        max_size_mb: int = 10,
        max_age_hours: int = 24,
        gzip_compress: bool = True,
    ):
        self.base_path = Path(base_path)
        self.max_size_mb = max_size_mb
        self.max_age_hours = max_age_hours
        self.gzip_compress = gzip_compress
        self.current_file = None
        self.written_count = 0
        self.rotation_count = 0
        self.start_time = time.time()

        # Ensure directory exists
        self.base_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event_dict: Dict[str, Any]) -> None:
        """Write event to rotating file (append & close)."""
        try:
            # Check if we need to rotate (based on on-disk size & age)
            if self._should_rotate():
                self._rotate_file()

            # Write event
            json_line = json.dumps(event_dict, separators=(",", ":"))
            if self.gzip_compress:
                with gzip.open(self.base_path, "at", encoding="utf-8") as f:
                    f.write(json_line + "\n")
            else:
                with open(self.base_path, "a", encoding="utf-8") as f:
                    f.write(json_line + "\n")
            self.written_count += 1

        except Exception as e:
            print(f"Error writing to rotating file {self.base_path}: {e}", file=sys.stderr)

    def flush(self) -> None:
        """Flush file buffer."""
        # No persistent handle, nothing to flush beyond OS cache

    def _should_rotate(self) -> bool:
        """Check if file should be rotated."""
        try:
            current_size = self.base_path.stat().st_size if self.base_path.exists() else 0
        except Exception as e:
            import logging
            logging.warning(f"Error checking base path size: {e}")
            current_size = 0
        size_limit = self.max_size_mb * 1024 * 1024

        # Check age
        age_hours = (time.time() - self.start_time) / 3600

        return current_size > size_limit or age_hours > self.max_age_hours

    def _rotate_file(self) -> None:
        """Rotate the current file."""
        # No persistent handle to close

        # Rename current file if it exists
        if self.base_path.exists():
            timestamp = int(time.time())
            rotated_path = self.base_path.with_suffix(f".{timestamp}.jsonl")
            if self.gzip_compress:
                rotated_path = rotated_path.with_suffix(".jsonl.gz")

            self.base_path.rename(rotated_path)
            self.rotation_count += 1
            self.start_time = time.time()

    def _open_file(self) -> None:
        """No persistent handle needed (compatibility)."""
        self.current_file = None

    def get_stats(self) -> Dict[str, Any]:
        """Get sink statistics."""
        return {
            "written": self.written_count,
            "rotations": self.rotation_count,
            "base_path": str(self.base_path),
        }

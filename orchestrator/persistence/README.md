# Persistence

Data persistence layer for the Xeno Mathematics Engine.

## Overview

The persistence layer handles storage and retrieval of proofs, capabilities, and system state. It provides a unified interface for data access across all components.

## Architecture

```
persistence/
├── base_storage.py      # Base storage interface
├── file_storage.py      # File-based storage
├── database_storage.py  # Database storage
├── cache_storage.py     # Caching layer
├── pack_storage.py      # Pack-based storage (PEFC)
└── backup_storage.py    # Backup and recovery
```

## Base Storage Interface

All storage implementations follow a common interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseStorage(ABC):
    """Base class for all storage implementations."""

    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def store(self, key: str, data: Any) -> bool:
        """Store data with the given key."""
        pass

    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data by key."""
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix."""
        pass
```

## Storage Types

### File Storage

File-based storage for local development and testing:

```python
import json
import os
from pathlib import Path

class FileStorage(BaseStorage):
    """File-based storage implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.base_path = Path(config.get('base_path', 'data/storage'))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store(self, key: str, data: Any) -> bool:
        """Store data to file."""
        try:
            file_path = self.base_path / f"{key}.json"
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error storing {key}: {e}")
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from file."""
        try:
            file_path = self.base_path / f"{key}.json"
            if not file_path.exists():
                return None
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error retrieving {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data file."""
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting {key}: {e}")
            return False

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix."""
        try:
            pattern = f"{prefix}*.json" if prefix else "*.json"
            files = list(self.base_path.glob(pattern))
            return [f.stem for f in files]
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []
```

### Database Storage

Database storage for production use:

```python
import sqlite3
from typing import Any, Dict, List, Optional

class DatabaseStorage(BaseStorage):
    """Database storage implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.db_path = config.get('db_path', 'data/xme.db')
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def store(self, key: str, data: Any) -> bool:
        """Store data in database."""
        try:
            import json
            data_json = json.dumps(data)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO storage (key, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                    (key, data_json)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error storing {key}: {e}")
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT data FROM storage WHERE key = ?', (key,))
                row = cursor.fetchone()
                if row:
                    import json
                    return json.loads(row[0])
                return None
        except Exception as e:
            print(f"Error retrieving {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM storage WHERE key = ?', (key,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting {key}: {e}")
            return False

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if prefix:
                    cursor = conn.execute('SELECT key FROM storage WHERE key LIKE ?', (f"{prefix}%",))
                else:
                    cursor = conn.execute('SELECT key FROM storage')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []
```

### Pack Storage (PEFC)

Pack-based storage for structured data:

```python
class PackStorage(BaseStorage):
    """Pack-based storage implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.pack_path = Path(config.get('pack_path', 'data/packs'))
        self.pack_path.mkdir(parents=True, exist_ok=True)

    def store(self, key: str, data: Any) -> bool:
        """Store data as a pack."""
        try:
            pack_path = self.pack_path / f"{key}.pack"
            # Implement pack creation logic
            return True
        except Exception as e:
            print(f"Error storing pack {key}: {e}")
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from pack."""
        try:
            pack_path = self.pack_path / f"{key}.pack"
            if not pack_path.exists():
                return None
            # Implement pack reading logic
            return None
        except Exception as e:
            print(f"Error retrieving pack {key}: {e}")
            return None
```

## Storage Manager

The storage manager coordinates different storage backends:

```python
class StorageManager:
    """Manages multiple storage backends."""

    def __init__(self, config):
        self.config = config
        self.storages = {}
        self._init_storages()

    def _init_storages(self):
        """Initialize storage backends."""
        for name, storage_config in self.config.get('storages', {}).items():
            storage_type = storage_config.get('type', 'file')
            if storage_type == 'file':
                self.storages[name] = FileStorage(storage_config)
            elif storage_type == 'database':
                self.storages[name] = DatabaseStorage(storage_config)
            elif storage_type == 'pack':
                self.storages[name] = PackStorage(storage_config)

    def get_storage(self, name: str) -> BaseStorage:
        """Get a storage backend by name."""
        if name not in self.storages:
            raise ValueError(f"Unknown storage: {name}")
        return self.storages[name]

    def store(self, storage_name: str, key: str, data: Any) -> bool:
        """Store data using specified storage."""
        storage = self.get_storage(storage_name)
        return storage.store(key, data)

    def retrieve(self, storage_name: str, key: str) -> Optional[Any]:
        """Retrieve data using specified storage."""
        storage = self.get_storage(storage_name)
        return storage.retrieve(key)
```

## Caching Layer

The caching layer provides performance optimization:

```python
import time
from typing import Any, Dict, Optional

class CacheStorage(BaseStorage):
    """Caching storage implementation."""

    def __init__(self, config):
        super().__init__(config)
        self.cache = {}
        self.ttl = config.get('ttl', 3600)  # Time to live in seconds

    def store(self, key: str, data: Any) -> bool:
        """Store data in cache."""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        return True

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from cache."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if time.time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None

        return entry['data']

    def delete(self, key: str) -> bool:
        """Delete data from cache."""
        if key in self.cache:
            del self.cache[key]
        return True

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with optional prefix."""
        keys = list(self.cache.keys())
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys
```

## Configuration

Storage can be configured through YAML files:

```yaml
persistence:
  default_storage: "file"

  storages:
    file:
      type: "file"
      base_path: "data/storage"

    database:
      type: "database"
      db_path: "data/xme.db"

    pack:
      type: "pack"
      pack_path: "data/packs"

    cache:
      type: "cache"
      ttl: 3600

  backup:
    enabled: true
    schedule: "daily"
    retention: 30
    path: "data/backups"
```

## Error Handling

Storage implementations include comprehensive error handling:

```python
class StorageError(Exception):
    """Base exception for storage errors."""
    pass

class StorageNotFoundError(StorageError):
    """Storage not found errors."""
    pass

class StorageAccessError(StorageError):
    """Storage access errors."""
    pass

class StorageCorruptionError(StorageError):
    """Storage corruption errors."""
    pass
```

## Future Enhancements

### Planned Features

- **Distributed Storage**: Support for distributed storage systems
- **Encryption**: Built-in encryption for sensitive data
- **Compression**: Automatic data compression
- **Replication**: Data replication for high availability

### Integration Points

- **Orchestrator**: Integration with workflow orchestration
- **Engines**: Integration with proof verification engines
- **Monitoring**: Integration with monitoring systems
- **Backup**: Integration with backup systems

## Development Status

This component is currently in the planning phase. The persistence layer will be implemented in Epic 2 as part of the core system architecture.

## References

- [Storage Design Document](storage-design.md)
- [Data Models](data-models.md)
- [Performance Guide](performance-guide.md)
- [API Reference](api-reference.md)

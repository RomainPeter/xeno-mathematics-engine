"""
Audit manifest and Merkle tree implementation for event persistence.
Provides AuditManifest and MerkleTree for integrity verification.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class FileInfo:
    """Information about a file in the audit manifest.

    Extended with role, created_at and source_hash to enrich provenance and
    enable stronger verification semantics.
    """

    path: str
    sha256: str
    bytes: int
    mtime: Optional[float] = None
    role: Optional[str] = None
    created_at: Optional[int] = None
    source_hash: Optional[str] = None


@dataclass
class AuditManifest:
    """Audit manifest for event persistence."""

    version: str = "1"
    run_id: str = ""
    created_ts: int = field(default_factory=lambda: int(time.time()))
    files: List[FileInfo] = field(default_factory=list)
    merkle_root: str = ""
    total_bytes: int = 0

    def add_file(
        self,
        file_path: str,
        sha256: str,
        bytes_count: int,
        mtime: Optional[float] = None,
        *,
        role: Optional[str] = None,
        created_at: Optional[int] = None,
        source_hash: Optional[str] = None,
    ):
        """Add a file to the manifest."""
        file_info = FileInfo(
            path=file_path,
            sha256=sha256,
            bytes=bytes_count,
            mtime=mtime,
            role=role,
            created_at=created_at,
            source_hash=source_hash,
        )
        self.files.append(file_info)
        self.total_bytes += bytes_count

    def _compute_merkle_root(self) -> str:
        """Compute the Merkle root from current file list without mutating state."""
        if not self.files:
            return ""

        sorted_files = sorted(self.files, key=lambda f: f.path)
        file_hashes: List[str] = [
            hashlib.sha256(file_info.sha256.encode()).hexdigest()
            for file_info in sorted_files
        ]

        if len(file_hashes) == 1:
            return file_hashes[0]

        current_level = file_hashes
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                    next_level.append(hashlib.sha256(combined.encode()).hexdigest())
                else:
                    next_level.append(current_level[i])
            current_level = next_level

        return current_level[0]

    def calculate_merkle_root(self) -> str:
        """Calculate and set the Merkle root hash."""
        self.merkle_root = self._compute_merkle_root()
        return self.merkle_root

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "version": self.version,
            "run_id": self.run_id,
            "created_ts": self.created_ts,
            "files": [
                {
                    "path": f.path,
                    "sha256": f.sha256,
                    "bytes": f.bytes,
                    "mtime": f.mtime,
                    "role": f.role,
                    "created_at": f.created_at,
                    "source_hash": f.source_hash,
                }
                for f in self.files
            ],
            "merkle_root": self.merkle_root,
            "total_bytes": self.total_bytes,
        }

    def to_json(self) -> str:
        """Convert manifest to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditManifest":
        """Create manifest from dictionary."""
        manifest = cls(
            version=data.get("version", "1"),
            run_id=data.get("run_id", ""),
            created_ts=data.get("created_ts", int(time.time())),
            merkle_root=data.get("merkle_root", ""),
            total_bytes=data.get("total_bytes", 0),
        )

        for file_data in data.get("files", []):
            manifest.add_file(
                file_path=file_data["path"],
                sha256=file_data["sha256"],
                bytes_count=file_data["bytes"],
                mtime=file_data.get("mtime"),
                role=file_data.get("role"),
                created_at=file_data.get("created_at"),
                source_hash=file_data.get("source_hash"),
            )

        return manifest

    @classmethod
    def from_json(cls, json_str: str) -> "AuditManifest":
        """Create manifest from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def verify_integrity(self) -> bool:
        """Verify the integrity of the manifest."""
        if not self.files:
            return True

        # Recompute Merkle root without mutating stored root
        calculated_root = self._compute_merkle_root()
        return calculated_root == self.merkle_root

    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Get information about a specific file."""
        for file_info in self.files:
            if file_info.path == file_path:
                return file_info
        return None

    def get_total_files(self) -> int:
        """Get total number of files."""
        return len(self.files)

    def get_total_size(self) -> int:
        """Get total size in bytes."""
        return self.total_bytes


class MerkleTree:
    """Merkle tree implementation for integrity verification."""

    def __init__(self, data: List[str]):
        self.data = data
        self.tree = self._build_tree()
        self.root = self.tree[-1] if self.tree else ""

    def _build_tree(self) -> List[str]:
        """Build the Merkle tree."""
        if not self.data:
            return []

        # Start with leaf hashes
        current_level = [
            hashlib.sha256(item.encode()).hexdigest() for item in self.data
        ]
        tree = current_level.copy()

        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Combine two hashes
                    combined = current_level[i] + current_level[i + 1]
                    next_level.append(hashlib.sha256(combined.encode()).hexdigest())
                else:
                    # Odd number of hashes, use the last one
                    next_level.append(current_level[i])
            tree.extend(next_level)
            current_level = next_level

        return tree

    def get_proof(self, index: int) -> List[str]:
        """Get Merkle proof for a specific index."""
        if index >= len(self.data):
            return []

        proof = []
        current_index = index
        level_start = 0
        level_size = len(self.data)

        while level_size > 1:
            # Find sibling
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1

            # Add sibling to proof if it exists
            if sibling_index < level_size:
                proof.append(self.tree[level_start + sibling_index])

            # Move to next level
            level_start += level_size
            current_index //= 2
            level_size = (level_size + 1) // 2

        return proof

    def verify_proof(self, index: int, proof: List[str], leaf_hash: str) -> bool:
        """Verify a Merkle proof."""
        if index >= len(self.data):
            return False

        current_hash = leaf_hash
        current_index = index
        level_size = len(self.data)
        proof_index = 0

        while level_size > 1:
            # Get sibling hash (empty if not provided)
            sibling_hash = proof[proof_index] if proof_index < len(proof) else ""

            # Combine hashes respecting left/right position
            if current_index % 2 == 0:
                combined = current_hash + sibling_hash
            else:
                combined = sibling_hash + current_hash

            current_hash = hashlib.sha256(combined.encode()).hexdigest()
            current_index //= 2
            level_size = (level_size + 1) // 2
            proof_index += 1

        return current_hash == self.root

    def get_root(self) -> str:
        """Get the Merkle root."""
        return self.root

    def get_tree(self) -> List[str]:
        """Get the entire tree."""
        return self.tree.copy()

    def get_leaf_count(self) -> int:
        """Get number of leaf nodes."""
        return len(self.data)

    def get_tree_height(self) -> int:
        """Get height of the tree."""
        if not self.data:
            return 0

        height = 0
        level_size = len(self.data)
        while level_size > 1:
            level_size = (level_size + 1) // 2
            height += 1

        return height


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def create_audit_manifest(
    run_id: str,
    audit_dir: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> AuditManifest:
    """Create an audit manifest for a directory."""
    manifest = AuditManifest(run_id=run_id)
    audit_path = Path(audit_dir)

    if not audit_path.exists():
        return manifest

    # Get all files
    all_files = []
    for file_path in audit_path.rglob("*"):
        if file_path.is_file():
            all_files.append(file_path)

    # Apply include/exclude patterns
    if include_patterns:
        import fnmatch

        filtered_files = []
        for file_path in all_files:
            for pattern in include_patterns:
                if fnmatch.fnmatch(str(file_path), pattern):
                    filtered_files.append(file_path)
                    break
        all_files = filtered_files

    if exclude_patterns:
        import fnmatch

        filtered_files = []
        for file_path in all_files:
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(file_path), pattern):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file_path)
        all_files = filtered_files

    # Add files to manifest
    for file_path in all_files:
        try:
            file_hash = calculate_file_hash(str(file_path))
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime

            # Get relative path from audit_dir
            rel_path = file_path.relative_to(audit_path)
            rel_str = str(rel_path).replace("\\", "/")
            # Derive a simple role from path
            role = _infer_role_from_path(rel_str)
            created_at = int(file_mtime) if file_mtime else None
            # When building from normalized inputs, source_hash may equal sha256
            source_hash = file_hash
            manifest.add_file(
                file_path=rel_str,
                sha256=file_hash,
                bytes_count=file_size,
                mtime=file_mtime,
                role=role,
                created_at=created_at,
                source_hash=source_hash,
            )
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    # Calculate Merkle root
    manifest.calculate_merkle_root()

    return manifest


def _infer_role_from_path(rel_path: str) -> str:
    """Infer a coarse role label from the relative path under the run directory."""
    if rel_path == "journal.jsonl":
        return "journal"
    if rel_path == "incidents.jsonl":
        return "incidents"
    if rel_path == "metrics.json":
        return "metrics"
    if rel_path == "manifest.json":
        return "manifest"
    if rel_path == "merkle.json":
        return "merkle"
    if rel_path == "provenance.json":
        return "provenance"
    if rel_path.startswith("pcaps/") or rel_path.startswith("pcap/"):
        return "pcap"
    if rel_path.startswith("inputs/"):
        return "input"
    if rel_path == "logs.jsonl":
        return "logs"
    return "artifact"


def build_merkle_dataset_from_manifest(manifest: AuditManifest) -> Dict[str, Any]:
    """Construct a deterministic Merkle dataset (order, leaves, proofs) from a manifest.

    - Order is sorted by file path
    - Leaves are sha256 of each file entry's sha256 (hex of hex as string, matching _compute_merkle_root)
    - Proofs are arrays of sibling hashes for each leaf index
    """
    if not manifest.files:
        return {"order": [], "leaves": [], "root": "", "proofs": []}

    # Important: pass raw sha256 hex strings to MerkleTree which will build leaf hashes
    sorted_files = sorted(manifest.files, key=lambda f: f.path)
    data = [f.sha256 for f in sorted_files]
    mt = MerkleTree(data)
    # Leaves as used by the tree (i.e., sha256 of each data item)
    leaves = [hashlib.sha256(x.encode()).hexdigest() for x in data]
    proofs = [mt.get_proof(i) for i in range(len(data))]
    return {
        "order": [f.path for f in sorted_files],
        "leaves": leaves,
        "root": mt.get_root(),
        "proofs": proofs,
    }

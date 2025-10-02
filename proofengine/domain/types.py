"""
Domain types for code compliance verification.
Defines Candidate, Verdict, Counterexample, and ComplianceRule types.
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ComplianceStatus(Enum):
    """Status of compliance verification."""

    OK = "ok"
    VIOLATION = "violation"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class CodeLocation:
    """Location in source code."""

    file_path: str
    line_number: int
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        if self.column is not None:
            return f"{self.file_path}:{self.line_number}:{self.column}"
        return f"{self.file_path}:{self.line_number}"

    def __repr__(self) -> str:
        return f"CodeLocation(file='{self.file_path}', line={self.line_number})"


@dataclass
class CodeSnippet:
    """Code snippet with context."""

    content: str
    language: str = "python"
    start_line: int = 1
    end_line: Optional[int] = None

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"CodeSnippet(language='{self.language}', lines={self.start_line}-{self.end_line})"


@dataclass
class Proof:
    """Proof of compliance or violation."""

    rule_id: str
    status: ComplianceStatus
    evidence: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Proof({self.rule_id}, {self.status.value}, confidence={self.confidence})"

    def __repr__(self) -> str:
        return (
            f"Proof(rule='{self.rule_id}', status={self.status.value}, evidence='{self.evidence}')"
        )


@dataclass
class Candidate:
    """Candidate solution for code compliance."""

    patch: str
    spec: str
    rationale: str
    seed: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Generate deterministic ID from seed
        if not hasattr(self, "_id"):
            self._id = hashlib.sha256(self.seed.encode()).hexdigest()[:16]

    @property
    def id(self) -> str:
        """Get candidate ID."""
        return self._id

    def __str__(self) -> str:
        return f"Candidate(id={self.id}, patch={len(self.patch)} chars)"

    def __repr__(self) -> str:
        return f"Candidate(id='{self.id}', rationale='{self.rationale[:50]}...')"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "patch": self.patch,
            "spec": self.spec,
            "rationale": self.rationale,
            "seed": self.seed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candidate":
        """Create from dictionary."""
        return cls(
            patch=data["patch"],
            spec=data["spec"],
            rationale=data["rationale"],
            seed=data["seed"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class Verdict:
    """Verdict from compliance verification."""

    status: ComplianceStatus
    proofs: List[Proof] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_ok(self) -> bool:
        """Check if verdict is OK."""
        return self.status == ComplianceStatus.OK

    @property
    def is_violation(self) -> bool:
        """Check if verdict is violation."""
        return self.status == ComplianceStatus.VIOLATION

    @property
    def confidence(self) -> float:
        """Get overall confidence."""
        if not self.proofs:
            return 0.0
        return sum(proof.confidence for proof in self.proofs) / len(self.proofs)

    def __str__(self) -> str:
        return f"Verdict({self.status.value}, {len(self.proofs)} proofs)"

    def __repr__(self) -> str:
        return f"Verdict(status={self.status.value}, proofs={len(self.proofs)}, confidence={self.confidence:.2f})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "proofs": [proof.__dict__ for proof in self.proofs],
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verdict":
        """Create from dictionary."""
        proofs = [Proof(**proof_data) for proof_data in data.get("proofs", [])]
        return cls(
            status=ComplianceStatus(data["status"]),
            proofs=proofs,
            execution_time=data.get("execution_time", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Counterexample:
    """Counterexample from compliance verification."""

    file_path: str
    line_number: int
    snippet: CodeSnippet
    rule: str
    violation_type: str
    severity: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def location(self) -> CodeLocation:
        """Get code location."""
        return CodeLocation(file_path=self.file_path, line_number=self.line_number)

    def __str__(self) -> str:
        return f"Counterexample({self.file_path}:{self.line_number}, rule={self.rule})"

    def __repr__(self) -> str:
        return (
            f"Counterexample(file='{self.file_path}', line={self.line_number}, rule='{self.rule}')"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "snippet": {
                "content": self.snippet.content,
                "language": self.snippet.language,
                "start_line": self.snippet.start_line,
                "end_line": self.snippet.end_line,
            },
            "rule": self.rule,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Counterexample":
        """Create from dictionary."""
        snippet_data = data["snippet"]
        snippet = CodeSnippet(
            content=snippet_data["content"],
            language=snippet_data.get("language", "python"),
            start_line=snippet_data.get("start_line", 1),
            end_line=snippet_data.get("end_line"),
        )
        return cls(
            file_path=data["file_path"],
            line_number=data["line_number"],
            snippet=snippet,
            rule=data["rule"],
            violation_type=data["violation_type"],
            severity=data.get("severity", "medium"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ComplianceRule:
    """Rule for code compliance verification."""

    id: str
    name: str
    description: str
    pattern: str
    severity: str = "medium"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"ComplianceRule(id={self.id}, name={self.name})"

    def __repr__(self) -> str:
        return f"ComplianceRule(id='{self.id}', name='{self.name}', enabled={self.enabled})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern": self.pattern,
            "severity": self.severity,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplianceRule":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            pattern=data["pattern"],
            severity=data.get("severity", "medium"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ComplianceResult:
    """Result of compliance verification."""

    verdict: Verdict
    counterexamples: List[Counterexample] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_compliant(self) -> bool:
        """Check if code is compliant."""
        return self.verdict.is_ok and not self.counterexamples

    @property
    def violation_count(self) -> int:
        """Get number of violations."""
        return len(self.counterexamples)

    def __str__(self) -> str:
        return f"ComplianceResult(compliant={self.is_compliant}, violations={self.violation_count})"

    def __repr__(self) -> str:
        return f"ComplianceResult(compliant={self.is_compliant}, violations={self.violation_count}, time={self.execution_time:.3f}s)"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "verdict": self.verdict.to_dict(),
            "counterexamples": [ce.to_dict() for ce in self.counterexamples],
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplianceResult":
        """Create from dictionary."""
        verdict = Verdict.from_dict(data["verdict"])
        counterexamples = [
            Counterexample.from_dict(ce_data) for ce_data in data.get("counterexamples", [])
        ]
        return cls(
            verdict=verdict,
            counterexamples=counterexamples,
            execution_time=data.get("execution_time", 0.0),
            metadata=data.get("metadata", {}),
        )

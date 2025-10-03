"""
FailReason emission for budget overruns and timeouts.
Provides structured failure reporting with severity levels.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FailReasonType(Enum):
    """FailReason types."""

    TIME_BUDGET_EXCEEDED = "time_budget_exceeded"
    MAX_ITERS_REACHED = "max_iters_reached"
    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"
    API_CALL_LIMIT_EXCEEDED = "api_call_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    VERIFICATION_FAILED = "verification_failed"
    SYNTHESIS_FAILED = "synthesis_failed"
    ORACLE_FAILED = "oracle_failed"
    CANCELLATION_REQUESTED = "cancellation_requested"
    UNKNOWN_ERROR = "unknown_error"


class FailReasonSeverity(Enum):
    """FailReason severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FailReason:
    """FailReason with structured information."""

    id: str
    type: FailReasonType
    severity: FailReasonSeverity
    message: str
    context: Dict[str, Any]
    timestamp: datetime
    component: str
    operation: str
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailReason":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=FailReasonType(data["type"]),
            severity=FailReasonSeverity(data["severity"]),
            message=data["message"],
            context=data["context"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            component=data["component"],
            operation=data["operation"],
            suggestions=data.get("suggestions", []),
            metadata=data.get("metadata", {}),
        )


class FailReasonFactory:
    """Factory for creating FailReason instances."""

    @staticmethod
    def create_time_budget_exceeded(
        component: str,
        operation: str,
        current_time: float,
        budget_limit: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create time budget exceeded FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.TIME_BUDGET_EXCEEDED,
            severity=FailReasonSeverity.HIGH,
            message=f"Time budget exceeded: {current_time:.2f}s > {budget_limit:.2f}s",
            context={
                "current_time": current_time,
                "budget_limit": budget_limit,
                "overrun": current_time - budget_limit,
                "percentage": (current_time / budget_limit) * 100,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Increase time budget",
                "Optimize algorithm performance",
                "Use parallel processing",
                "Reduce problem complexity",
            ],
            metadata={"budget_type": "time"},
        )

    @staticmethod
    def create_max_iters_reached(
        component: str,
        operation: str,
        current_iters: int,
        max_iters: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create max iterations reached FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.MAX_ITERS_REACHED,
            severity=FailReasonSeverity.MEDIUM,
            message=f"Maximum iterations reached: {current_iters} >= {max_iters}",
            context={
                "current_iters": current_iters,
                "max_iters": max_iters,
                "convergence_rate": current_iters / max_iters,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Increase max iterations",
                "Improve convergence algorithm",
                "Adjust convergence criteria",
                "Use different optimization strategy",
            ],
            metadata={"budget_type": "iterations"},
        )

    @staticmethod
    def create_token_budget_exceeded(
        component: str,
        operation: str,
        current_tokens: int,
        budget_limit: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create token budget exceeded FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.TOKEN_BUDGET_EXCEEDED,
            severity=FailReasonSeverity.HIGH,
            message=f"Token budget exceeded: {current_tokens} > {budget_limit}",
            context={
                "current_tokens": current_tokens,
                "budget_limit": budget_limit,
                "overrun": current_tokens - budget_limit,
                "percentage": (current_tokens / budget_limit) * 100,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Reduce prompt length",
                "Use smaller model",
                "Implement prompt compression",
                "Increase token budget",
            ],
            metadata={"budget_type": "tokens"},
        )

    @staticmethod
    def create_timeout_exceeded(
        component: str,
        operation: str,
        timeout_duration: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create timeout exceeded FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.TIMEOUT_EXCEEDED,
            severity=FailReasonSeverity.MEDIUM,
            message=f"Operation timed out after {timeout_duration:.2f}s",
            context={
                "timeout_duration": timeout_duration,
                "operation_type": operation,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Increase timeout duration",
                "Optimize operation performance",
                "Use asynchronous processing",
                "Implement progress monitoring",
            ],
            metadata={"budget_type": "timeout"},
        )

    @staticmethod
    def create_verification_failed(
        component: str,
        operation: str,
        failure_reason: str,
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create verification failed FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.VERIFICATION_FAILED,
            severity=FailReasonSeverity.HIGH,
            message=f"Verification failed: {failure_reason}",
            context={
                "failure_reason": failure_reason,
                "evidence": evidence,
                "evidence_count": len(evidence),
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Review implementation",
                "Check specification requirements",
                "Verify constraints",
                "Improve test coverage",
            ],
            metadata={"failure_type": "verification"},
        )

    @staticmethod
    def create_synthesis_failed(
        component: str,
        operation: str,
        failure_reason: str,
        attempts: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create synthesis failed FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.SYNTHESIS_FAILED,
            severity=FailReasonSeverity.HIGH,
            message=f"Synthesis failed: {failure_reason}",
            context={
                "failure_reason": failure_reason,
                "attempts": attempts,
                "success_rate": 0.0,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Improve synthesis algorithm",
                "Adjust synthesis parameters",
                "Use different synthesis strategy",
                "Increase synthesis attempts",
            ],
            metadata={"failure_type": "synthesis"},
        )

    @staticmethod
    def create_oracle_failed(
        component: str,
        operation: str,
        failure_reason: str,
        oracle_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create oracle failed FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.ORACLE_FAILED,
            severity=FailReasonSeverity.CRITICAL,
            message=f"Oracle failed: {failure_reason}",
            context={
                "failure_reason": failure_reason,
                "oracle_type": oracle_type,
                "component": component,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Check oracle configuration",
                "Verify oracle connectivity",
                "Review oracle implementation",
                "Implement oracle fallback",
            ],
            metadata={"failure_type": "oracle", "oracle_type": oracle_type},
        )

    @staticmethod
    def create_cancellation_requested(
        component: str,
        operation: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create cancellation requested FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.CANCELLATION_REQUESTED,
            severity=FailReasonSeverity.LOW,
            message=f"Operation cancelled: {reason}",
            context={
                "cancellation_reason": reason,
                "component": component,
                "operation": operation,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Review cancellation logic",
                "Implement graceful shutdown",
                "Save intermediate results",
                "Clean up resources",
            ],
            metadata={"failure_type": "cancellation"},
        )

    @staticmethod
    def create_unknown_error(
        component: str,
        operation: str,
        error: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> FailReason:
        """Create unknown error FailReason."""
        return FailReason(
            id=str(uuid.uuid4()),
            type=FailReasonType.UNKNOWN_ERROR,
            severity=FailReasonSeverity.CRITICAL,
            message=f"Unknown error: {error}",
            context={
                "error": error,
                "component": component,
                "operation": operation,
                **(context or {}),
            },
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            suggestions=[
                "Review error logs",
                "Check system configuration",
                "Verify input data",
                "Contact support",
            ],
            metadata={"failure_type": "unknown"},
        )

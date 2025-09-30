"""
Budget management with exponential backoff.
Provides budget tracking and overrun detection.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class BudgetType(Enum):
    """Budget types."""

    TIME = "time"
    TOKENS = "tokens"
    API_CALLS = "api_calls"
    MEMORY = "memory"
    CUSTOM = "custom"


class BudgetStatus(Enum):
    """Budget status."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERRUN = "overrun"


@dataclass
class BudgetConfig:
    """Configuration for budget management."""

    default_timeout: float = 30.0
    warning_threshold: float = 0.8  # 80% of budget
    critical_threshold: float = 0.95  # 95% of budget
    overrun_threshold: float = 1.0  # 100% of budget
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    jitter_range: float = 0.1
    enable_warnings: bool = True
    enable_automatic_scaling: bool = False


@dataclass
class Budget:
    """Budget definition."""

    budget_type: BudgetType
    limit: float
    current: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetStatus:
    """Budget status information."""

    budget_type: BudgetType
    current: float
    limit: float
    percentage: float
    status: BudgetStatus
    overrun: bool
    warning: bool
    critical: bool
    time_remaining: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)


class BudgetManager:
    """Budget manager with exponential backoff and overrun detection."""

    def __init__(self, config: BudgetConfig):
        self.config = config
        self.budgets: Dict[BudgetType, Budget] = {}
        self.status_history: List[BudgetStatus] = []
        self.backoff_delays: Dict[BudgetType, float] = {}
        self.initialized = False

        # Callbacks
        self.warning_callbacks: List[Callable] = []
        self.overrun_callbacks: List[Callable] = []

    async def start(self) -> None:
        """Start budget manager."""
        self.initialized = True

    async def stop(self) -> None:
        """Stop budget manager."""
        self.initialized = False

    async def set_budget(self, budget_config: Dict[str, Any]) -> None:
        """Set budget limits."""
        for budget_type_str, limit in budget_config.items():
            budget_type = BudgetType(budget_type_str)

            budget = Budget(
                budget_type=budget_type,
                limit=limit,
                current=0.0,
                start_time=datetime.now(),
            )

            self.budgets[budget_type] = budget
            self.backoff_delays[budget_type] = 0.0

    async def consume_budget(
        self, budget_type: BudgetType, amount: float, operation: str = "unknown"
    ) -> bool:
        """Consume budget and check for overrun."""
        if not self.initialized:
            raise RuntimeError("Budget manager not initialized")

        if budget_type not in self.budgets:
            return True  # No budget set for this type

        budget = self.budgets[budget_type]
        budget.current += amount

        # Check budget status
        status = await self._check_budget_status(budget_type)

        if status.overrun:
            # Handle overrun
            await self._handle_budget_overrun(budget_type, status, operation)
            return False
        elif status.critical:
            # Apply backoff
            await self._apply_backoff(budget_type)
        elif status.warning:
            # Emit warning
            await self._emit_warning(budget_type, status, operation)

        return True

    async def check_budget_available(self, budget_type: BudgetType, required_amount: float) -> bool:
        """Check if budget is available for required amount."""
        if budget_type not in self.budgets:
            return True  # No budget set

        budget = self.budgets[budget_type]
        return (budget.current + required_amount) <= budget.limit

    async def get_budget_status(self, budget_type: BudgetType) -> BudgetStatus:
        """Get current budget status."""
        if budget_type not in self.budgets:
            return BudgetStatus(
                budget_type=budget_type,
                current=0.0,
                limit=float("inf"),
                percentage=0.0,
                status=BudgetStatus.OK,
                overrun=False,
                warning=False,
                critical=False,
            )

        budget = self.budgets[budget_type]
        percentage = budget.current / budget.limit

        if percentage >= self.config.overrun_threshold:
            status = BudgetStatus.OVERRUN
            overrun = True
            warning = False
            critical = False
        elif percentage >= self.config.critical_threshold:
            status = BudgetStatus.CRITICAL
            overrun = False
            warning = False
            critical = True
        elif percentage >= self.config.warning_threshold:
            status = BudgetStatus.WARNING
            overrun = False
            warning = True
            critical = False
        else:
            status = BudgetStatus.OK
            overrun = False
            warning = False
            critical = False

        # Calculate time remaining for time budgets
        time_remaining = None
        if budget_type == BudgetType.TIME and budget.start_time:
            elapsed = (datetime.now() - budget.start_time).total_seconds()
            time_remaining = max(0, budget.limit - elapsed)

        # Generate suggestions
        suggestions = await self._generate_suggestions(budget_type, percentage, status)

        return BudgetStatus(
            budget_type=budget_type,
            current=budget.current,
            limit=budget.limit,
            percentage=percentage,
            status=status,
            overrun=overrun,
            warning=warning,
            critical=critical,
            time_remaining=time_remaining,
            suggestions=suggestions,
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get overall budget status."""
        statuses = {}

        for budget_type in self.budgets:
            status = await self.get_budget_status(budget_type)
            statuses[budget_type.value] = {
                "current": status.current,
                "limit": status.limit,
                "percentage": status.percentage,
                "status": status.status.value,
                "overrun": status.overrun,
                "warning": status.warning,
                "critical": status.critical,
                "time_remaining": status.time_remaining,
                "suggestions": status.suggestions,
            }

        return {
            "budgets": statuses,
            "config": {
                "warning_threshold": self.config.warning_threshold,
                "critical_threshold": self.config.critical_threshold,
                "overrun_threshold": self.config.overrun_threshold,
                "backoff_base": self.config.backoff_base,
                "max_backoff": self.config.max_backoff,
            },
            "backoff_delays": self.backoff_delays,
        }

    async def _check_budget_status(self, budget_type: BudgetType) -> BudgetStatus:
        """Check budget status and update history."""
        status = await self.get_budget_status(budget_type)
        self.status_history.append(status)

        # Keep only recent history
        if len(self.status_history) > 100:
            self.status_history = self.status_history[-100:]

        return status

    async def _handle_budget_overrun(
        self, budget_type: BudgetType, status: BudgetStatus, operation: str
    ) -> None:
        """Handle budget overrun."""
        # Apply maximum backoff
        self.backoff_delays[budget_type] = self.config.max_backoff

        # Call overrun callbacks
        for callback in self.overrun_callbacks:
            try:
                await callback(budget_type, status, operation)
            except Exception as e:
                print(f"Error in overrun callback: {e}")

    async def _apply_backoff(self, budget_type: BudgetType) -> None:
        """Apply exponential backoff."""
        current_delay = self.backoff_delays.get(budget_type, 0.0)
        new_delay = min(current_delay * self.config.backoff_base, self.config.max_backoff)

        # Add jitter
        jitter = self.config.jitter_range * (0.5 - time.time() % 1)
        new_delay += jitter

        self.backoff_delays[budget_type] = new_delay

        # Apply delay
        await asyncio.sleep(new_delay)

    async def _emit_warning(
        self, budget_type: BudgetType, status: BudgetStatus, operation: str
    ) -> None:
        """Emit budget warning."""
        if not self.config.enable_warnings:
            return

        # Call warning callbacks
        for callback in self.warning_callbacks:
            try:
                await callback(budget_type, status, operation)
            except Exception as e:
                print(f"Error in warning callback: {e}")

    async def _generate_suggestions(
        self, budget_type: BudgetType, percentage: float, status: BudgetStatus
    ) -> List[str]:
        """Generate suggestions based on budget status."""
        suggestions = []

        if status == BudgetStatus.OVERRUN:
            suggestions.extend(
                [
                    "Budget overrun detected",
                    "Consider reducing operation frequency",
                    "Review budget allocation",
                    "Implement more efficient algorithms",
                ]
            )
        elif status == BudgetStatus.CRITICAL:
            suggestions.extend(
                [
                    "Budget critical (95%+ used)",
                    "Consider pausing non-essential operations",
                    "Monitor budget consumption closely",
                    "Prepare for potential overrun",
                ]
            )
        elif status == BudgetStatus.WARNING:
            suggestions.extend(
                [
                    "Budget warning (80%+ used)",
                    "Monitor budget consumption",
                    "Consider optimizing operations",
                    "Plan for budget management",
                ]
            )

        # Type-specific suggestions
        if budget_type == BudgetType.TIME:
            suggestions.append("Consider parallelizing operations")
        elif budget_type == BudgetType.TOKENS:
            suggestions.append("Consider using smaller models or shorter prompts")
        elif budget_type == BudgetType.API_CALLS:
            suggestions.append("Consider batching API calls")
        elif budget_type == BudgetType.MEMORY:
            suggestions.append("Consider reducing memory usage or increasing allocation")

        return suggestions

    def add_warning_callback(self, callback: Callable) -> None:
        """Add warning callback."""
        self.warning_callbacks.append(callback)

    def add_overrun_callback(self, callback: Callable) -> None:
        """Add overrun callback."""
        self.overrun_callbacks.append(callback)

    async def reset_budget(self, budget_type: BudgetType) -> None:
        """Reset budget to initial state."""
        if budget_type in self.budgets:
            self.budgets[budget_type].current = 0.0
            self.budgets[budget_type].start_time = datetime.now()
            self.backoff_delays[budget_type] = 0.0

    async def reset_all_budgets(self) -> None:
        """Reset all budgets."""
        for budget_type in self.budgets:
            await self.reset_budget(budget_type)

    async def cleanup(self) -> None:
        """Cleanup budget manager."""
        self.budgets.clear()
        self.status_history.clear()
        self.backoff_delays.clear()
        self.warning_callbacks.clear()
        self.overrun_callbacks.clear()
        self.initialized = False

"""
Async scheduler with asyncio.gather and timeouts.
Provides concurrent execution with proper cancellation safety.
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .budget_manager import BudgetManager, BudgetConfig
from .task_manager import TaskManager, TaskStatus, TaskResult


class SchedulerStatus(Enum):
    """Scheduler status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class SchedulerConfig:
    """Configuration for async scheduler."""

    max_concurrent_tasks: int = 10
    default_timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_base: float = 2.0
    retry_jitter: float = 0.1
    cancellation_timeout: float = 5.0
    enable_budget_management: bool = True
    enable_task_persistence: bool = True


@dataclass
class SchedulerStats:
    """Scheduler statistics."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    timeout_tasks: int = 0
    average_execution_time: float = 0.0
    total_execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class AsyncScheduler:
    """Async scheduler with concurrent execution and timeout management."""

    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.status = SchedulerStatus.IDLE
        self.stats = SchedulerStats()

        # Components
        self.budget_manager = (
            BudgetManager(BudgetConfig()) if config.enable_budget_management else None
        )
        self.task_manager = TaskManager() if config.enable_task_persistence else None

        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, Exception] = {}

        # Synchronization
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the scheduler."""
        async with self._lock:
            if self.status != SchedulerStatus.IDLE:
                raise RuntimeError(f"Scheduler is not idle (status: {self.status})")

            self.status = SchedulerStatus.RUNNING
            self.stats.start_time = datetime.now()

            if self.budget_manager:
                await self.budget_manager.start()

            if self.task_manager:
                await self.task_manager.start()

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        async with self._lock:
            if self.status not in [SchedulerStatus.RUNNING, SchedulerStatus.PAUSED]:
                return

            self.status = SchedulerStatus.STOPPING

            # Cancel all active tasks
            await self._cancel_all_tasks()

            # Stop components
            if self.budget_manager:
                await self.budget_manager.stop()

            if self.task_manager:
                await self.task_manager.stop()

            self.status = SchedulerStatus.STOPPED
            self.stats.end_time = datetime.now()

    async def execute_concurrent(
        self,
        tasks: List[Callable],
        timeouts: Optional[List[float]] = None,
        task_names: Optional[List[str]] = None,
        **kwargs,
    ) -> List[TaskResult]:
        """Execute multiple tasks concurrently with timeouts."""
        if self.status != SchedulerStatus.RUNNING:
            raise RuntimeError(f"Scheduler is not running (status: {self.status})")

        # Prepare task configurations
        task_configs = []
        for i, task in enumerate(tasks):
            config = {
                "task": task,
                "timeout": (
                    timeouts[i] if timeouts and i < len(timeouts) else self.config.default_timeout
                ),
                "name": (task_names[i] if task_names and i < len(task_names) else f"task_{i}"),
                "kwargs": kwargs,
            }
            task_configs.append(config)

        # Execute tasks concurrently
        return await self._execute_tasks_concurrent(task_configs)

    async def execute_with_budget(
        self,
        tasks: List[Callable],
        budget_config: Dict[str, Any],
        timeouts: Optional[List[float]] = None,
        task_names: Optional[List[str]] = None,
        **kwargs,
    ) -> List[TaskResult]:
        """Execute tasks with budget management."""
        if not self.budget_manager:
            raise RuntimeError("Budget management not enabled")

        # Set budget
        await self.budget_manager.set_budget(budget_config)

        # Execute tasks
        results = await self.execute_concurrent(tasks, timeouts, task_names, **kwargs)

        # Check budget status
        budget_status = await self.budget_manager.get_status()
        if budget_status.overrun:
            # Handle budget overrun
            await self._handle_budget_overrun(budget_status)

        return results

    async def _execute_tasks_concurrent(
        self, task_configs: List[Dict[str, Any]]
    ) -> List[TaskResult]:
        """Execute tasks concurrently with proper timeout and cancellation handling."""
        task_ids = []
        asyncio_tasks = []

        # Create asyncio tasks
        for config in task_configs:
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)

            asyncio_task = asyncio.create_task(self._execute_single_task(task_id, config))
            asyncio_tasks.append(asyncio_task)

            # Track active task
            self.active_tasks[task_id] = asyncio_task

        try:
            # Wait for all tasks to complete with timeout
            results = await asyncio.gather(*asyncio_tasks, return_exceptions=True)

            # Process results
            task_results = []
            for i, result in enumerate(results):
                task_id = task_ids[i]

                if isinstance(result, Exception):
                    # Task failed
                    self.failed_tasks[task_id] = result
                    task_result = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        result=None,
                        error=str(result),
                        execution_time=0.0,
                    )
                else:
                    # Task completed
                    task_result = result
                    if task_result.status == TaskStatus.COMPLETED:
                        self.completed_tasks[task_id] = task_result
                    else:
                        self.failed_tasks[task_id] = Exception(task_result.error)

                task_results.append(task_result)

            return task_results

        finally:
            # Clean up active tasks
            for task_id in task_ids:
                self.active_tasks.pop(task_id, None)

    async def _execute_single_task(self, task_id: str, config: Dict[str, Any]) -> TaskResult:
        """Execute a single task with timeout and retry logic."""
        task = config["task"]
        timeout = config["timeout"]
        name = config["name"]
        kwargs = config["kwargs"]

        start_time = datetime.now()
        retry_count = 0
        last_exception = None

        while retry_count <= self.config.max_retries:
            try:
                # Execute task with timeout
                result = await asyncio.wait_for(task(**kwargs), timeout=timeout)

                # Task completed successfully
                execution_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(TaskStatus.COMPLETED, execution_time)

                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    error=None,
                    execution_time=execution_time,
                    metadata={
                        "name": name,
                        "retry_count": retry_count,
                        "timeout": timeout,
                    },
                )

            except asyncio.TimeoutError:
                # Task timed out
                execution_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(TaskStatus.TIMEOUT, execution_time)

                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.TIMEOUT,
                    result=None,
                    error=f"Task timed out after {timeout}s",
                    execution_time=execution_time,
                    metadata={
                        "name": name,
                        "retry_count": retry_count,
                        "timeout": timeout,
                    },
                )

            except asyncio.CancelledError:
                # Task was cancelled
                execution_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(TaskStatus.CANCELLED, execution_time)

                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.CANCELLED,
                    result=None,
                    error="Task was cancelled",
                    execution_time=execution_time,
                    metadata={
                        "name": name,
                        "retry_count": retry_count,
                        "timeout": timeout,
                    },
                )

            except Exception as e:
                last_exception = e
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    # Retry with exponential backoff
                    delay = self.config.retry_delay * (
                        self.config.retry_backoff_base ** (retry_count - 1)
                    )
                    jitter = self.config.retry_jitter * (0.5 - asyncio.get_event_loop().time() % 1)
                    await asyncio.sleep(delay + jitter)
                else:
                    # Max retries exceeded
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._update_stats(TaskStatus.FAILED, execution_time)

                    return TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        result=None,
                        error=f"Task failed after {retry_count} retries: {str(last_exception)}",
                        execution_time=execution_time,
                        metadata={
                            "name": name,
                            "retry_count": retry_count,
                            "timeout": timeout,
                            "last_exception": str(last_exception),
                        },
                    )

        # This should never be reached
        raise RuntimeError("Unexpected state in task execution")

    async def _cancel_all_tasks(self) -> None:
        """Cancel all active tasks safely."""
        if not self.active_tasks:
            return

        # Cancel all tasks
        for task_id, task in self.active_tasks.items():
            if not task.done():
                task.cancel()

        # Wait for cancellation with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks.values(), return_exceptions=True),
                timeout=self.config.cancellation_timeout,
            )
        except asyncio.TimeoutError:
            # Some tasks didn't cancel in time, log warning
            pass

        # Clear active tasks
        self.active_tasks.clear()

    async def _handle_budget_overrun(self, budget_status: Any) -> None:
        """Handle budget overrun."""
        # Cancel remaining tasks
        await self._cancel_all_tasks()

        # Update status
        self.status = SchedulerStatus.ERROR

        # Log budget overrun
        print(f"Budget overrun detected: {budget_status}")

    def _update_stats(self, status: TaskStatus, execution_time: float) -> None:
        """Update scheduler statistics."""
        self.stats.total_tasks += 1

        if status == TaskStatus.COMPLETED:
            self.stats.completed_tasks += 1
        elif status == TaskStatus.FAILED:
            self.stats.failed_tasks += 1
        elif status == TaskStatus.CANCELLED:
            self.stats.cancelled_tasks += 1
        elif status == TaskStatus.TIMEOUT:
            self.stats.timeout_tasks += 1

        # Update average execution time
        self.stats.total_execution_time += execution_time
        self.stats.average_execution_time = self.stats.total_execution_time / self.stats.total_tasks

    async def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "status": self.status.value,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "stats": {
                "total_tasks": self.stats.total_tasks,
                "completed_tasks": self.stats.completed_tasks,
                "failed_tasks": self.stats.failed_tasks,
                "cancelled_tasks": self.stats.cancelled_tasks,
                "timeout_tasks": self.stats.timeout_tasks,
                "average_execution_time": self.stats.average_execution_time,
                "total_execution_time": self.stats.total_execution_time,
            },
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "default_timeout": self.config.default_timeout,
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
            },
        }

    async def cleanup(self) -> None:
        """Cleanup scheduler resources."""
        await self.stop()

        if self.budget_manager:
            await self.budget_manager.cleanup()

        if self.task_manager:
            await self.task_manager.cleanup()

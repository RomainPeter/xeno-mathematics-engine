"""
Task manager with safe cancellation.
Provides task tracking and safe cancellation of remaining tasks.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TaskStatus(Enum):
    """Task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TaskResult:
    """Task execution result."""

    task_id: str
    status: TaskStatus
    result: Any
    error: Optional[str]
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskInfo:
    """Task information."""

    task_id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    asyncio_task: Optional[asyncio.Task] = None
    result: Optional[TaskResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """Task manager with safe cancellation."""

    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        self.cancelled_tasks: Dict[str, TaskResult] = {}

        # Cancellation safety
        self._cancellation_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._cancellation_timeout = 5.0

        self.initialized = False

    async def start(self) -> None:
        """Start task manager."""
        self.initialized = True

    async def stop(self) -> None:
        """Stop task manager and cancel all tasks."""
        if not self.initialized:
            return

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel all tasks safely
        await self.cancel_all_tasks()

        self.initialized = False

    async def create_task(
        self, coro: Callable, name: str, timeout: Optional[float] = None, **kwargs
    ) -> str:
        """Create a new task."""
        if not self.initialized:
            raise RuntimeError("Task manager not initialized")

        task_id = str(uuid.uuid4())

        # Create asyncio task
        asyncio_task = asyncio.create_task(self._execute_task(task_id, coro, timeout, **kwargs))

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            asyncio_task=asyncio_task,
            metadata={"timeout": timeout, "kwargs": kwargs},
        )

        self.tasks[task_id] = task_info
        return task_id

    async def wait_for_task(self, task_id: str) -> TaskResult:
        """Wait for a specific task to complete."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task_info = self.tasks[task_id]

        if task_info.asyncio_task:
            try:
                await task_info.asyncio_task
            except Exception as e:
                # Task failed
                if task_id not in self.failed_tasks:
                    self.failed_tasks[task_id] = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        result=None,
                        error=str(e),
                        execution_time=0.0,
                    )

        # Return result if available
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        elif task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        elif task_id in self.cancelled_tasks:
            return self.cancelled_tasks[task_id]
        else:
            # Task still running
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                result=None,
                error=None,
                execution_time=0.0,
            )

    async def cancel_task(self, task_id: str, reason: str = "manual_cancellation") -> bool:
        """Cancel a specific task safely."""
        if task_id not in self.tasks:
            return False

        task_info = self.tasks[task_id]

        if task_info.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return False  # Task already finished

        # Cancel asyncio task
        if task_info.asyncio_task and not task_info.asyncio_task.done():
            task_info.asyncio_task.cancel()

            # Wait for cancellation with timeout
            try:
                await asyncio.wait_for(task_info.asyncio_task, timeout=self._cancellation_timeout)
            except asyncio.TimeoutError:
                # Task didn't cancel in time
                pass
            except asyncio.CancelledError:
                # Task was cancelled successfully
                pass

        # Update task status
        task_info.status = TaskStatus.CANCELLED
        task_info.completed_at = datetime.now()

        # Create cancellation result
        execution_time = 0.0
        if task_info.started_at:
            execution_time = (task_info.completed_at - task_info.started_at).total_seconds()

        cancellation_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.CANCELLED,
            result=None,
            error=f"Task cancelled: {reason}",
            execution_time=execution_time,
            metadata={"cancellation_reason": reason},
        )

        self.cancelled_tasks[task_id] = cancellation_result
        task_info.result = cancellation_result

        return True

    async def cancel_all_tasks(self, reason: str = "shutdown") -> int:
        """Cancel all running tasks safely."""
        async with self._cancellation_lock:
            cancelled_count = 0

            for task_id, task_info in self.tasks.items():
                if task_info.status == TaskStatus.RUNNING:
                    if await self.cancel_task(task_id, reason):
                        cancelled_count += 1

            return cancelled_count

    async def cancel_tasks_by_name(self, name: str, reason: str = "bulk_cancellation") -> int:
        """Cancel all tasks with a specific name."""
        cancelled_count = 0

        for task_id, task_info in self.tasks.items():
            if task_info.name == name and task_info.status == TaskStatus.RUNNING:
                if await self.cancel_task(task_id, reason):
                    cancelled_count += 1

        return cancelled_count

    async def _execute_task(
        self, task_id: str, coro: Callable, timeout: Optional[float], **kwargs
    ) -> TaskResult:
        """Execute a task with proper error handling."""
        task_info = self.tasks[task_id]
        start_time = datetime.now()

        try:
            # Update task status
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = start_time

            # Execute task with timeout if specified
            if timeout:
                result = await asyncio.wait_for(coro(**kwargs), timeout=timeout)
            else:
                result = await coro(**kwargs)

            # Task completed successfully
            execution_time = (datetime.now() - start_time).total_seconds()
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                error=None,
                execution_time=execution_time,
                metadata={"timeout": timeout, "kwargs": kwargs},
            )

            self.completed_tasks[task_id] = task_result
            task_info.result = task_result

            return task_result

        except asyncio.TimeoutError:
            # Task timed out
            execution_time = (datetime.now() - start_time).total_seconds()
            task_info.status = TaskStatus.TIMEOUT
            task_info.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.TIMEOUT,
                result=None,
                error=f"Task timed out after {timeout}s",
                execution_time=execution_time,
                metadata={"timeout": timeout, "kwargs": kwargs},
            )

            self.failed_tasks[task_id] = task_result
            task_info.result = task_result

            return task_result

        except asyncio.CancelledError:
            # Task was cancelled
            execution_time = (datetime.now() - start_time).total_seconds()
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
                result=None,
                error="Task was cancelled",
                execution_time=execution_time,
                metadata={"timeout": timeout, "kwargs": kwargs},
            )

            self.cancelled_tasks[task_id] = task_result
            task_info.result = task_result

            return task_result

        except Exception as e:
            # Task failed
            execution_time = (datetime.now() - start_time).total_seconds()
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                result=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"timeout": timeout, "kwargs": kwargs},
            )

            self.failed_tasks[task_id] = task_result
            task_info.result = task_result

            return task_result

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status."""
        if task_id not in self.tasks:
            return None

        return self.tasks[task_id].status

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        elif task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        elif task_id in self.cancelled_tasks:
            return self.cancelled_tasks[task_id]
        else:
            return None

    async def get_all_tasks(self) -> List[TaskInfo]:
        """Get all task information."""
        return list(self.tasks.values())

    async def get_running_tasks(self) -> List[TaskInfo]:
        """Get all running tasks."""
        return [
            task_info for task_info in self.tasks.values() if task_info.status == TaskStatus.RUNNING
        ]

    async def get_completed_tasks(self) -> List[TaskResult]:
        """Get all completed tasks."""
        return list(self.completed_tasks.values())

    async def get_failed_tasks(self) -> List[TaskResult]:
        """Get all failed tasks."""
        return list(self.failed_tasks.values())

    async def get_cancelled_tasks(self) -> List[TaskResult]:
        """Get all cancelled tasks."""
        return list(self.cancelled_tasks.values())

    async def get_statistics(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        total_tasks = len(self.tasks)
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        completed_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        cancelled_tasks = len(self.cancelled_tasks)

        return {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "cancelled_tasks": cancelled_tasks,
            "success_rate": completed_tasks / max(total_tasks, 1),
            "failure_rate": failed_tasks / max(total_tasks, 1),
            "cancellation_rate": cancelled_tasks / max(total_tasks, 1),
        }

    async def cleanup(self) -> None:
        """Cleanup task manager."""
        await self.stop()

        self.tasks.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()
        self.cancelled_tasks.clear()

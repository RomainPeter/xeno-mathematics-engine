# Scheduler

Task scheduling and execution management for the Xeno Mathematics Engine.

## Overview

The scheduler manages task scheduling, execution, and resource allocation for the Xeno Mathematics Engine. It provides a unified interface for scheduling proof verification tasks, managing dependencies, and optimizing resource usage.

## Architecture

```
scheduler/
├── base_scheduler.py    # Base scheduler interface
├── task_scheduler.py     # Task scheduling implementation
├── resource_scheduler.py # Resource management
├── dependency_scheduler.py # Dependency management
├── priority_scheduler.py # Priority-based scheduling
└── distributed_scheduler.py # Distributed scheduling
```

## Base Scheduler Interface

All schedulers implement a common interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
import time

class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority enumeration."""
    LOWEST = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    HIGHEST = 5

class BaseScheduler(ABC):
    """Base class for all schedulers."""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
        self.tasks = {}
        self.resources = {}
    
    @abstractmethod
    def schedule_task(self, task: Dict[str, Any]) -> str:
        """Schedule a task for execution."""
        pass
    
    @abstractmethod
    def execute_task(self, task_id: str) -> bool:
        """Execute a scheduled task."""
        pass
    
    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        pass
    
    @abstractmethod
    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get the status of a task."""
        pass
```

## Task Scheduler

The task scheduler manages individual tasks:

```python
import uuid
from concurrent.futures import ThreadPoolExecutor, Future

class TaskScheduler(BaseScheduler):
    """Task scheduling implementation."""
    
    def __init__(self, config):
        super().__init__(config)
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_workers', 4))
        self.futures = {}
    
    def schedule_task(self, task: Dict[str, Any]) -> str:
        """Schedule a task for execution."""
        task_id = str(uuid.uuid4())
        
        # Create task record
        task_record = {
            'id': task_id,
            'name': task.get('name', 'unnamed'),
            'type': task.get('type', 'generic'),
            'priority': task.get('priority', TaskPriority.NORMAL),
            'status': TaskStatus.PENDING,
            'created_at': time.time(),
            'scheduled_at': time.time(),
            'config': task.get('config', {}),
            'dependencies': task.get('dependencies', []),
            'result': None,
            'error': None
        }
        
        self.tasks[task_id] = task_record
        
        # Schedule for execution
        self._schedule_execution(task_id)
        
        return task_id
    
    def execute_task(self, task_id: str) -> bool:
        """Execute a scheduled task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Check dependencies
        if not self._check_dependencies(task):
            return False
        
        # Update status
        task['status'] = TaskStatus.RUNNING
        task['started_at'] = time.time()
        
        # Submit to executor
        future = self.executor.submit(self._execute_task_impl, task)
        self.futures[task_id] = future
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # Cancel if running
        if task['status'] == TaskStatus.RUNNING and task_id in self.futures:
            self.futures[task_id].cancel()
        
        # Update status
        task['status'] = TaskStatus.CANCELLED
        task['cancelled_at'] = time.time()
        
        return True
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get the status of a task."""
        if task_id not in self.tasks:
            return TaskStatus.FAILED
        
        return self.tasks[task_id]['status']
    
    def _schedule_execution(self, task_id: str):
        """Schedule task for execution."""
        # Implement scheduling logic
        pass
    
    def _check_dependencies(self, task: Dict[str, Any]) -> bool:
        """Check if task dependencies are satisfied."""
        for dep_id in task.get('dependencies', []):
            if dep_id not in self.tasks:
                return False
            dep_status = self.tasks[dep_id]['status']
            if dep_status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _execute_task_impl(self, task: Dict[str, Any]) -> Any:
        """Execute the actual task implementation."""
        try:
            # Get task type and execute accordingly
            task_type = task.get('type', 'generic')
            
            if task_type == 'proof_verification':
                return self._execute_proof_verification(task)
            elif task_type == 'capability_check':
                return self._execute_capability_check(task)
            elif task_type == 'data_processing':
                return self._execute_data_processing(task)
            else:
                return self._execute_generic_task(task)
                
        except Exception as e:
            task['error'] = str(e)
            task['status'] = TaskStatus.FAILED
            raise
        finally:
            task['completed_at'] = time.time()
            task['status'] = TaskStatus.COMPLETED
    
    def _execute_proof_verification(self, task: Dict[str, Any]) -> Any:
        """Execute proof verification task."""
        # Implement proof verification logic
        pass
    
    def _execute_capability_check(self, task: Dict[str, Any]) -> Any:
        """Execute capability check task."""
        # Implement capability check logic
        pass
    
    def _execute_data_processing(self, task: Dict[str, Any]) -> Any:
        """Execute data processing task."""
        # Implement data processing logic
        pass
    
    def _execute_generic_task(self, task: Dict[str, Any]) -> Any:
        """Execute generic task."""
        # Implement generic task logic
        pass
```

## Resource Scheduler

The resource scheduler manages system resources:

```python
class ResourceScheduler(BaseScheduler):
    """Resource management scheduler."""
    
    def __init__(self, config):
        super().__init__(config)
        self.resource_pools = {
            'cpu': config.get('cpu_cores', 4),
            'memory': config.get('memory_gb', 8),
            'disk': config.get('disk_gb', 100),
            'network': config.get('network_bandwidth', 1000)
        }
        self.allocated_resources = {}
    
    def schedule_task(self, task: Dict[str, Any]) -> str:
        """Schedule a task with resource requirements."""
        task_id = str(uuid.uuid4())
        
        # Check resource availability
        required_resources = task.get('resources', {})
        if not self._check_resource_availability(required_resources):
            raise ValueError("Insufficient resources for task")
        
        # Allocate resources
        self._allocate_resources(task_id, required_resources)
        
        # Create task record
        task_record = {
            'id': task_id,
            'name': task.get('name', 'unnamed'),
            'type': task.get('type', 'generic'),
            'priority': task.get('priority', TaskPriority.NORMAL),
            'status': TaskStatus.PENDING,
            'created_at': time.time(),
            'scheduled_at': time.time(),
            'config': task.get('config', {}),
            'resources': required_resources,
            'result': None,
            'error': None
        }
        
        self.tasks[task_id] = task_record
        return task_id
    
    def _check_resource_availability(self, required_resources: Dict[str, Any]) -> bool:
        """Check if required resources are available."""
        for resource_type, required_amount in required_resources.items():
            if resource_type not in self.resource_pools:
                return False
            
            available = self.resource_pools[resource_type]
            allocated = sum(self.allocated_resources.get(resource_type, {}).values())
            
            if available - allocated < required_amount:
                return False
        
        return True
    
    def _allocate_resources(self, task_id: str, resources: Dict[str, Any]):
        """Allocate resources for a task."""
        for resource_type, amount in resources.items():
            if resource_type not in self.allocated_resources:
                self.allocated_resources[resource_type] = {}
            self.allocated_resources[resource_type][task_id] = amount
    
    def _deallocate_resources(self, task_id: str):
        """Deallocate resources for a task."""
        for resource_type in self.allocated_resources:
            if task_id in self.allocated_resources[resource_type]:
                del self.allocated_resources[resource_type][task_id]
```

## Dependency Scheduler

The dependency scheduler manages task dependencies:

```python
class DependencyScheduler(BaseScheduler):
    """Dependency management scheduler."""
    
    def __init__(self, config):
        super().__init__(config)
        self.dependency_graph = {}
        self.ready_tasks = set()
    
    def schedule_task(self, task: Dict[str, Any]) -> str:
        """Schedule a task with dependencies."""
        task_id = str(uuid.uuid4())
        
        # Create task record
        task_record = {
            'id': task_id,
            'name': task.get('name', 'unnamed'),
            'type': task.get('type', 'generic'),
            'priority': task.get('priority', TaskPriority.NORMAL),
            'status': TaskStatus.PENDING,
            'created_at': time.time(),
            'scheduled_at': time.time(),
            'config': task.get('config', {}),
            'dependencies': task.get('dependencies', []),
            'dependents': [],
            'result': None,
            'error': None
        }
        
        self.tasks[task_id] = task_record
        
        # Build dependency graph
        self._build_dependency_graph(task_id, task_record['dependencies'])
        
        # Check if task is ready to run
        if self._is_task_ready(task_id):
            self.ready_tasks.add(task_id)
        
        return task_id
    
    def _build_dependency_graph(self, task_id: str, dependencies: List[str]):
        """Build the dependency graph."""
        self.dependency_graph[task_id] = dependencies
        
        # Update dependents
        for dep_id in dependencies:
            if dep_id in self.tasks:
                if 'dependents' not in self.tasks[dep_id]:
                    self.tasks[dep_id]['dependents'] = []
                self.tasks[dep_id]['dependents'].append(task_id)
    
    def _is_task_ready(self, task_id: str) -> bool:
        """Check if a task is ready to run."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        dependencies = task.get('dependencies', [])
        
        for dep_id in dependencies:
            if dep_id not in self.tasks:
                return False
            if self.tasks[dep_id]['status'] != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to run."""
        return list(self.ready_tasks)
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed and update dependents."""
        if task_id not in self.tasks:
            return
        
        self.tasks[task_id]['status'] = TaskStatus.COMPLETED
        
        # Check dependents
        dependents = self.tasks[task_id].get('dependents', [])
        for dep_id in dependents:
            if self._is_task_ready(dep_id):
                self.ready_tasks.add(dep_id)
```

## Priority Scheduler

The priority scheduler manages task priorities:

```python
import heapq

class PriorityScheduler(BaseScheduler):
    """Priority-based scheduling."""
    
    def __init__(self, config):
        super().__init__(config)
        self.priority_queue = []
        self.task_priorities = {}
    
    def schedule_task(self, task: Dict[str, Any]) -> str:
        """Schedule a task with priority."""
        task_id = str(uuid.uuid4())
        
        # Create task record
        task_record = {
            'id': task_id,
            'name': task.get('name', 'unnamed'),
            'type': task.get('type', 'generic'),
            'priority': task.get('priority', TaskPriority.NORMAL),
            'status': TaskStatus.PENDING,
            'created_at': time.time(),
            'scheduled_at': time.time(),
            'config': task.get('config', {}),
            'result': None,
            'error': None
        }
        
        self.tasks[task_id] = task_record
        
        # Add to priority queue
        priority = task_record['priority'].value
        heapq.heappush(self.priority_queue, (priority, task_id))
        self.task_priorities[task_id] = priority
        
        return task_id
    
    def get_next_task(self) -> Optional[str]:
        """Get the next task to execute based on priority."""
        if not self.priority_queue:
            return None
        
        # Get highest priority task
        priority, task_id = heapq.heappop(self.priority_queue)
        
        # Check if task is still valid
        if task_id not in self.tasks:
            return self.get_next_task()
        
        if self.tasks[task_id]['status'] != TaskStatus.PENDING:
            return self.get_next_task()
        
        return task_id
    
    def update_task_priority(self, task_id: str, new_priority: TaskPriority):
        """Update task priority."""
        if task_id not in self.tasks:
            return False
        
        old_priority = self.task_priorities.get(task_id, TaskPriority.NORMAL)
        self.task_priorities[task_id] = new_priority.value
        
        # Re-add to queue with new priority
        heapq.heappush(self.priority_queue, (new_priority.value, task_id))
        
        return True
```

## Configuration

Schedulers can be configured through YAML files:

```yaml
scheduler:
  type: "task"  # task, resource, dependency, priority, distributed
  
  task_scheduler:
    max_workers: 4
    timeout: 300
    retry_attempts: 3
    
  resource_scheduler:
    cpu_cores: 4
    memory_gb: 8
    disk_gb: 100
    network_bandwidth: 1000
    
  dependency_scheduler:
    max_dependency_depth: 10
    dependency_timeout: 600
    
  priority_scheduler:
    default_priority: "normal"
    priority_boost: 1.2
    
  distributed_scheduler:
    nodes: ["node1", "node2", "node3"]
    load_balancing: "round_robin"
    failover: true
```

## Error Handling

Schedulers include comprehensive error handling:

```python
class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass

class TaskSchedulingError(SchedulerError):
    """Task scheduling errors."""
    pass

class ResourceAllocationError(SchedulerError):
    """Resource allocation errors."""
    pass

class DependencyError(SchedulerError):
    """Dependency management errors."""
    pass
```

## Future Enhancements

### Planned Features

- **Distributed Scheduling**: Support for distributed task execution
- **Load Balancing**: Advanced load balancing algorithms
- **Resource Optimization**: ML-based resource optimization
- **Fault Tolerance**: Enhanced fault tolerance and recovery

### Integration Points

- **Orchestrator**: Integration with workflow orchestration
- **Engines**: Integration with proof verification engines
- **Monitoring**: Integration with monitoring systems
- **Resource Management**: Integration with resource management systems

## Development Status

This component is currently in the planning phase. The scheduler will be implemented in Epic 2 as part of the core system architecture.

## References

- [Scheduler Design Document](scheduler-design.md)
- [Task Examples](task-examples.md)
- [Performance Guide](performance-guide.md)
- [API Reference](api-reference.md)

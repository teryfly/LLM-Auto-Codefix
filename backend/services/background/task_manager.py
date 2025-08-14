import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.api_models import TaskStatusResponse

logger = logging.getLogger("task_manager")

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackgroundTask:
    def __init__(self, task_id: str, name: str, func: Callable, *args, **kwargs):
        self.task_id = task_id
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[str] = None
        self.logs: List[str] = []
        self.asyncio_task: Optional[asyncio.Task] = None

    async def run(self):
        """Execute the background task"""
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.utcnow()
            self.add_log(f"Task {self.task_id} started")

            if asyncio.iscoroutinefunction(self.func):
                self.result = await self.func(*self.args, **self.kwargs)
            else:
                self.result = self.func(*self.args, **self.kwargs)

            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            self.add_log(f"Task {self.task_id} completed successfully")

        except asyncio.CancelledError:
            self.status = TaskStatus.CANCELLED
            self.completed_at = datetime.utcnow()
            self.add_log(f"Task {self.task_id} was cancelled")
            raise
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.utcnow()
            self.error = str(e)
            self.add_log(f"Task {self.task_id} failed: {e}")
            logger.error(f"Task {self.task_id} failed: {e}", exc_info=True)

    def add_log(self, message: str):
        """Add a log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(log_entry)

    def cancel(self):
        """Cancel the task"""
        if self.asyncio_task and not self.asyncio_task.done():
            self.asyncio_task.cancel()
            self.add_log(f"Task {self.task_id} cancellation requested")

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.max_completed_tasks = 100  # Keep only recent completed tasks

    def create_task(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Create and start a new background task"""
        task_id = str(uuid.uuid4())
        task = BackgroundTask(task_id, name, func, *args, **kwargs)
        self.tasks[task_id] = task

        # Start the task
        task.asyncio_task = asyncio.create_task(task.run())

        logger.info(f"Created and started task {task_id}: {name}")
        return task_id

    def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return TaskStatusResponse(
            task_id=task.task_id,
            name=task.name,
            status=task.status,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error=task.error,
            result=task.result
        )

    def list_tasks(self, status_filter: Optional[str] = None) -> List[TaskStatusResponse]:
        """List all tasks, optionally filtered by status"""
        tasks = []
        for task in self.tasks.values():
            if status_filter is None or task.status == status_filter:
                tasks.append(TaskStatusResponse(
                    task_id=task.task_id,
                    name=task.name,
                    status=task.status,
                    created_at=task.created_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    error=task.error
                ))

        # Sort by creation time, newest first
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError(f"Task {task_id} is already {task.status}")

        task.cancel()
        return {
            "task_id": task_id,
            "status": "cancellation_requested",
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_task_logs(self, task_id: str, offset: int = 0, limit: int = 100) -> List[str]:
        """Get logs for a specific task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return task.logs[offset:offset+limit]

    def cleanup_completed_tasks(self) -> int:
        """Clean up old completed tasks"""
        completed_tasks = [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]

        if len(completed_tasks) > self.max_completed_tasks:
            completed_tasks.sort(key=lambda x: x.completed_at)
            for task in completed_tasks[:-self.max_completed_tasks]:
                del self.tasks[task.task_id]
            removed_count = len(completed_tasks) - self.max_completed_tasks
        else:
            removed_count = 0

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old completed tasks")

        return removed_count
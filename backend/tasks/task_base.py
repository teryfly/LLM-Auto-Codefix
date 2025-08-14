import asyncio
import logging
from typing import Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger("task_base")

class BaseTask(ABC):
    """Base class for all background tasks"""

    def __init__(self, task_id: str, name: str):
        self.task_id = task_id
        self.name = name
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = "pending"
        self.result: Any = None
        self.error: Optional[str] = None
        self.logs: List[str] = []
        self.progress: float = 0.0
        self.metadata: dict = {}

    @abstractmethod
    async def execute(self) -> Any:
        """Execute the task logic - must be implemented by subclasses"""
        pass

    async def run(self) -> Any:
        """Run the task with error handling and logging"""
        try:
            self.status = "running"
            self.started_at = datetime.utcnow()
            self.add_log(f"Task {self.task_id} started")

            # Execute the actual task logic
            self.result = await self.execute()

            self.status = "completed"
            self.completed_at = datetime.utcnow()
            self.progress = 100.0
            self.add_log(f"Task {self.task_id} completed successfully")

            return self.result

        except asyncio.CancelledError:
            self.status = "cancelled"
            self.completed_at = datetime.utcnow()
            self.add_log(f"Task {self.task_id} was cancelled")
            raise

        except Exception as e:
            self.status = "failed"
            self.completed_at = datetime.utcnow()
            self.error = str(e)
            self.add_log(f"Task {self.task_id} failed: {e}")
            logger.error(f"Task {self.task_id} failed: {e}", exc_info=True)
            raise

    def add_log(self, message: str):
        """Add a log entry with timestamp"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(f"[{self.task_id}] {message}")

    def update_progress(self, progress: float, message: Optional[str] = None):
        """Update task progress"""
        self.progress = min(100.0, max(0.0, progress))
        if message:
            self.add_log(f"Progress: {self.progress:.1f}% - {message}")

    def set_metadata(self, key: str, value: Any):
        """Set metadata for the task"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)

    def get_status_info(self) -> dict:
        """Get comprehensive task status information"""
        duration = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            duration = (end_time - self.started_at).total_seconds()

        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": duration,
            "error": self.error,
            "metadata": self.metadata,
            "log_count": len(self.logs)
        }

    def get_logs(self, offset: int = 0, limit: int = 100) -> List[str]:
        """Get task logs with pagination"""
        return self.logs[offset:offset+limit]

    def is_completed(self) -> bool:
        """Check if task is completed (success, failed, or cancelled)"""
        return self.status in ["completed", "failed", "cancelled"]

    def is_running(self) -> bool:
        """Check if task is currently running"""
        return self.status == "running"
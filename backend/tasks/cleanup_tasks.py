import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from tasks.task_base import BaseTask

logger = logging.getLogger("cleanup_tasks")

class SessionCleanupTask(BaseTask):
    """Task for cleaning up expired sessions"""

    def __init__(self, session_service):
        super().__init__("session_cleanup", "Session Cleanup")
        self.session_service = session_service

    async def execute(self) -> Dict[str, Any]:
        """Clean up expired sessions"""
        try:
            self.add_log("Starting session cleanup")

            cleaned_count = self.session_service.cleanup_expired_sessions()

            self.add_log(f"Cleaned up {cleaned_count} expired sessions")
            return {"cleaned_sessions": cleaned_count}

        except Exception as e:
            self.add_log(f"Session cleanup failed: {e}")
            raise

class WorkflowStateCleanupTask(BaseTask):
    """Task for cleaning up old workflow states"""

    def __init__(self, workflow_state_manager, keep_hours: int = 24):
        super().__init__("workflow_state_cleanup", "Workflow State Cleanup")
        self.workflow_state_manager = workflow_state_manager
        self.keep_hours = keep_hours

    async def execute(self) -> Dict[str, Any]:
        """Clean up old workflow states"""
        try:
            self.add_log(f"Starting workflow state cleanup (keeping {self.keep_hours} hours)")

            cleaned_count = self.workflow_state_manager.clear_completed_workflows(self.keep_hours)

            self.add_log(f"Cleaned up {cleaned_count} old workflow states")
            return {"cleaned_workflows": cleaned_count}

        except Exception as e:
            self.add_log(f"Workflow state cleanup failed: {e}")
            raise

class TaskHistoryCleanupTask(BaseTask):
    """Task for cleaning up old task history"""

    def __init__(self, task_manager, keep_hours: int = 48):
        super().__init__("task_history_cleanup", "Task History Cleanup")
        self.task_manager = task_manager
        self.keep_hours = keep_hours

    async def execute(self) -> Dict[str, Any]:
        """Clean up old completed tasks"""
        try:
            self.add_log(f"Starting task history cleanup (keeping {self.keep_hours} hours)")

            cleaned_count = self.task_manager.cleanup_completed_tasks()

            self.add_log(f"Cleaned up {cleaned_count} old tasks")
            return {"cleaned_tasks": cleaned_count}

        except Exception as e:
            self.add_log(f"Task history cleanup failed: {e}")
            raise

class LogFileCleanupTask(BaseTask):
    """Task for cleaning up old log files"""

    def __init__(self, log_directory: str, keep_days: int = 7):
        super().__init__("log_file_cleanup", "Log File Cleanup")
        self.log_directory = Path(log_directory)
        self.keep_days = keep_days

    async def execute(self) -> Dict[str, Any]:
        """Clean up old log files"""
        try:
            self.add_log(f"Starting log file cleanup in {self.log_directory}")

            if not self.log_directory.exists():
                self.add_log("Log directory does not exist")
                return {"cleaned_files": 0}

            cutoff_time = datetime.now() - timedelta(days=self.keep_days)
            cleaned_files = 0

            for log_file in self.log_directory.glob("*.log*"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        log_file.unlink()
                        cleaned_files += 1

            self.add_log(f"Cleaned up {cleaned_files} old log files")
            return {"cleaned_files": cleaned_files}

        except Exception as e:
            self.add_log(f"Log file cleanup failed: {e}")
            raise

class ComprehensiveSystemCleanupTask(BaseTask):
    """Comprehensive system cleanup task"""

    def __init__(self, session_service, workflow_state_manager, task_manager, log_directory: str):
        super().__init__("comprehensive_system_cleanup", "Comprehensive System Cleanup")
        self.session_service = session_service
        self.workflow_state_manager = workflow_state_manager
        self.task_manager = task_manager
        self.log_directory = log_directory

    async def execute(self) -> Dict[str, Any]:
        """Run comprehensive system cleanup"""
        try:
            self.add_log("Starting comprehensive system cleanup")

            results = {}

            # Clean up sessions
            session_task = SessionCleanupTask(self.session_service)
            session_result = await session_task.execute()
            results["sessions"] = session_result

            # Clean up workflow states
            workflow_task = WorkflowStateCleanupTask(self.workflow_state_manager)
            workflow_result = await workflow_task.execute()
            results["workflows"] = workflow_result

            # Clean up task history
            task_task = TaskHistoryCleanupTask(self.task_manager)
            task_result = await task_task.execute()
            results["tasks"] = task_result

            # Clean up log files
            log_task = LogFileCleanupTask(self.log_directory)
            log_result = await log_task.execute()
            results["logs"] = log_result

            total_cleaned = (
                session_result.get("cleaned_sessions", 0) +
                workflow_result.get("cleaned_workflows", 0) +
                task_result.get("cleaned_tasks", 0) +
                log_result.get("cleaned_files", 0)
            )

            self.add_log(f"System cleanup completed. Total items cleaned: {total_cleaned}")
            results["total_cleaned"] = total_cleaned

            return results

        except Exception as e:
            self.add_log(f"System cleanup failed: {e}")
            raise
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.api_models import TaskStatusResponse, TaskListResponse
from services.background.task_manager import TaskManager
from ..core.dependencies import get_config

router = APIRouter()

# Global task manager instance
_task_manager: Optional[TaskManager] = None

def get_task_manager():
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status_filter: Optional[str] = None,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """List all background tasks"""
    try:
        tasks = task_manager.list_tasks(status_filter)
        return TaskListResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """Get status of a specific task"""
    try:
        task_status = task_manager.get_task_status(task_id)
        return task_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """Cancel a running task"""
    try:
        result = task_manager.cancel_task(task_id)
        return {"status": "cancelled", "message": "Task cancelled successfully", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )

@router.get("/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    offset: int = 0,
    limit: int = 100,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """Get logs for a specific task"""
    try:
        logs = task_manager.get_task_logs(task_id, offset, limit)
        return {"task_id": task_id, "logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task logs not found: {str(e)}"
        )
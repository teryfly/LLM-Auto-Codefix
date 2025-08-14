from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.api_models import (
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
    WorkflowStopRequest
)
from services.web.workflow_service import WorkflowService
from services.web.session_service import SessionService
from ..core.dependencies import get_workflow_service, get_session_service

router = APIRouter()

@router.post("/workflow/start", response_model=WorkflowStartResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
    session_service: SessionService = Depends(get_session_service)
):
    """Start a new workflow execution"""
    try:
        session_id = session_service.create_session()
        workflow_service.start_workflow(session_id, request)
        return WorkflowStartResponse(
            session_id=session_id,
            status="started",
            message="Workflow started successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )

@router.get("/workflow/status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Get current workflow status"""
    try:
        status_info = workflow_service.get_workflow_status(session_id)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found or error: {str(e)}"
        )

@router.post("/workflow/stop/{session_id}")
async def stop_workflow(
    session_id: str,
    request: WorkflowStopRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Stop a running workflow"""
    try:
        workflow_service.stop_workflow(session_id, request.force)
        return {"status": "stopped", "message": "Workflow stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop workflow: {str(e)}"
        )

@router.get("/workflow/logs/{session_id}")
async def get_workflow_logs(
    session_id: str,
    offset: int = 0,
    limit: int = 100,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow execution logs"""
    try:
        logs = workflow_service.get_workflow_logs(session_id, offset, limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Logs not found: {str(e)}"
        )
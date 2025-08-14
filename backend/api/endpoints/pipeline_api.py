from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.api_models import PipelineStatusResponse, JobStatusResponse
from services.web.pipeline_monitor_service import PipelineMonitorService
from ..core.dependencies import get_pipeline_monitor_service

router = APIRouter()

@router.get("/pipeline/{session_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    session_id: str,
    pipeline_service: PipelineMonitorService = Depends(get_pipeline_monitor_service)
):
    """Get current pipeline status for a session"""
    try:
        status_info = pipeline_service.get_pipeline_status(session_id)
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline status not found: {str(e)}"
        )

@router.get("/pipeline/{session_id}/jobs", response_model=list[JobStatusResponse])
async def get_job_statuses(
    session_id: str,
    pipeline_service: PipelineMonitorService = Depends(get_pipeline_monitor_service)
):
    """Get job statuses for a session's pipeline"""
    try:
        jobs = pipeline_service.get_job_statuses(session_id)
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job statuses not found: {str(e)}"
        )

@router.get("/pipeline/{session_id}/monitor")
async def monitor_pipeline(
    session_id: str,
    pipeline_service: PipelineMonitorService = Depends(get_pipeline_monitor_service)
):
    """Get comprehensive pipeline monitoring data"""
    try:
        monitor_data = pipeline_service.get_monitor_data(session_id)
        return monitor_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor data not found: {str(e)}"
        )

@router.post("/pipeline/{session_id}/retry")
async def retry_failed_jobs(
    session_id: str,
    pipeline_service: PipelineMonitorService = Depends(get_pipeline_monitor_service)
):
    """Retry failed jobs in the pipeline"""
    try:
        result = pipeline_service.retry_failed_jobs(session_id)
        return {"status": "retrying", "message": "Failed jobs retry initiated", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry jobs: {str(e)}"
        )

@router.get("/pipeline/{session_id}/trace/{job_id}")
async def get_job_trace(
    session_id: str,
    job_id: int,
    pipeline_service: PipelineMonitorService = Depends(get_pipeline_monitor_service)
):
    """Get trace output for a specific job"""
    try:
        trace = pipeline_service.get_job_trace(session_id, job_id)
        return {"job_id": job_id, "trace": trace}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job trace not found: {str(e)}"
        )
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict, Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from services.web.gitlab_proxy_service import GitLabProxyService
from ..core.dependencies import get_gitlab_proxy_service

router = APIRouter()

@router.get("/gitlab/projects/{project_path:path}")
async def get_project(
    project_path: str,
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab project API"""
    try:
        result = gitlab_service.get_project(project_path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {str(e)}"
        )

@router.get("/gitlab/projects/{project_id}/pipelines")
async def list_pipelines(
    project_id: int,
    ref: Optional[str] = None,
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab pipelines API"""
    try:
        params = {"ref": ref} if ref else {}
        result = gitlab_service.list_pipelines(project_id, params)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pipelines: {str(e)}"
        )

@router.get("/gitlab/projects/{project_id}/pipelines/{pipeline_id}")
async def get_pipeline(
    project_id: int,
    pipeline_id: int,
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab pipeline details API"""
    try:
        result = gitlab_service.get_pipeline(project_id, pipeline_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {str(e)}"
        )

@router.get("/gitlab/projects/{project_id}/pipelines/{pipeline_id}/jobs")
async def list_jobs(
    project_id: int,
    pipeline_id: int,
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab jobs API"""
    try:
        result = gitlab_service.list_jobs(project_id, pipeline_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch jobs: {str(e)}"
        )

@router.get("/gitlab/projects/{project_id}/jobs/{job_id}/trace")
async def get_job_trace(
    project_id: int,
    job_id: int,
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab job trace API"""
    try:
        result = gitlab_service.get_job_trace(project_id, job_id)
        return {"trace": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job trace not found: {str(e)}"
        )

@router.post("/gitlab/projects/{project_id}/merge_requests")
async def create_merge_request(
    project_id: int,
    request_data: Dict[str, Any],
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab merge request creation API"""
    try:
        result = gitlab_service.create_merge_request(project_id, request_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create merge request: {str(e)}"
        )

@router.put("/gitlab/projects/{project_id}/merge_requests/{mr_iid}/merge")
async def merge_merge_request(
    project_id: int,
    mr_iid: int,
    request_data: Dict[str, Any],
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab merge request merge API"""
    try:
        result = gitlab_service.merge_merge_request(project_id, mr_iid, request_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge request: {str(e)}"
        )

@router.post("/gitlab/projects/{project_id}/pipeline")
async def create_pipeline(
    project_id: int,
    request_data: Dict[str, Any],
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
):
    """Proxy GitLab pipeline creation API"""
    try:
        result = gitlab_service.create_pipeline(project_id, request_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}"
        )
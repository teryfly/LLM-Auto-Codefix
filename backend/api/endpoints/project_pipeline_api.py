from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from clients.gitlab.project_client import ProjectClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.gitlab.job_client import JobClient
from clients.gitlab.merge_request_client import MergeRequestClient
router = APIRouter()
@router.get("/projects/{project_path}")
async def get_project_info(project_path: str):
    """Get project information by path"""
    try:
        # URL decode project path
        actual_project_path = project_path.replace('%2F', '/')
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_path)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_path}' not found"
            )
        return {
            "id": project.id,
            "name": project.name,
            "path_with_namespace": project.path_with_namespace,
            "web_url": project.web_url,
            "default_branch": project.default_branch,
            "visibility": project.visibility
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project info: {str(e)}"
        )
@router.get("/projects/{project_id}/pipelines")
async def get_project_pipelines(project_id: int, per_page: int = 10, ref: str = None):
    """Get pipelines for a project"""
    try:
        pipeline_client = PipelineClient()
        params = {"per_page": per_page}
        if ref:
            params["ref"] = ref
        pipelines = pipeline_client.list_pipelines(project_id, ref, params)
        return [
            {
                "id": pipeline.id,
                "status": pipeline.status,
                "ref": pipeline.ref,
                "sha": pipeline.sha,
                "web_url": pipeline.web_url,
                "created_at": pipeline.created_at,
                "updated_at": pipeline.updated_at
            }
            for pipeline in pipelines
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipelines: {str(e)}"
        )
@router.get("/projects/{project_id}/pipelines/{pipeline_id}")
async def get_pipeline_info(project_id: int, pipeline_id: int):
    """Get specific pipeline information"""
    try:
        pipeline_client = PipelineClient()
        pipeline = pipeline_client.get_pipeline(project_id, pipeline_id)
        return {
            "id": pipeline.id,
            "status": pipeline.status,
            "ref": pipeline.ref,
            "sha": pipeline.sha,
            "web_url": pipeline.web_url,
            "created_at": pipeline.created_at,
            "updated_at": pipeline.updated_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline {pipeline_id} not found: {str(e)}"
        )
@router.get("/projects/{project_id}/pipelines/{pipeline_id}/jobs")
async def get_pipeline_jobs(project_id: int, pipeline_id: int):
    """Get jobs for a specific pipeline"""
    try:
        job_client = JobClient()
        jobs = job_client.list_jobs(project_id, pipeline_id)
        return [
            {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "stage": job.stage,
                "ref": job.ref,
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "web_url": job.web_url
            }
            for job in jobs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline jobs: {str(e)}"
        )
@router.get("/projects/{project_id}/jobs/{job_id}")
async def get_job_info(project_id: int, job_id: int):
    """Get specific job information"""
    try:
        job_client = JobClient()
        job = job_client.get_job_details(project_id, job_id)
        return {
            "id": job.id,
            "name": job.name,
            "status": job.status,
            "stage": job.stage,
            "ref": job.ref,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "web_url": job.web_url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found: {str(e)}"
        )
@router.get("/projects/{project_id}/jobs/{job_id}/trace")
async def get_job_trace(project_id: int, job_id: int):
    """Get job trace/logs"""
    try:
        job_client = JobClient()
        trace = job_client.get_job_trace(project_id, job_id)
        return trace
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job trace: {str(e)}"
        )
@router.post("/projects/{project_id}/merge_requests")
async def create_merge_request(
    project_id: int,
    data: Dict[str, Any]
):
    """Create a merge request"""
    try:
        mr_client = MergeRequestClient()
        source_branch = data.get("source_branch")
        target_branch = data.get("target_branch")
        title = data.get("title")
        if not all([source_branch, target_branch, title]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_branch, target_branch, and title are required"
            )
        mr = mr_client.create_merge_request(project_id, source_branch, target_branch, title)
        return {
            "id": mr.id,
            "iid": mr.iid,
            "project_id": mr.project_id,
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "state": mr.state,
            "title": mr.title,
            "web_url": mr.web_url,
            "created_at": mr.created_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create merge request: {str(e)}"
        )
@router.put("/projects/{project_id}/merge_requests/{merge_request_iid}/merge")
async def merge_merge_request(
    project_id: int,
    merge_request_iid: int,
    data: Dict[str, Any] = None
):
    """Merge a merge request"""
    try:
        mr_client = MergeRequestClient()
        result = mr_client.merge_mr(project_id, merge_request_iid)
        return result
    except ValueError as e:
        # Handle expected merge failures
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge request: {str(e)}"
        )
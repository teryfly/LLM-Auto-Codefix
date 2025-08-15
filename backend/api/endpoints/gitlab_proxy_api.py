from fastapi import APIRouter, Depends, HTTPException, status
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from clients.gitlab.project_client import ProjectClient
from clients.gitlab.merge_request_client import MergeRequestClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.gitlab.job_client import JobClient
router = APIRouter()
@router.get("/projects/{project_name}")
async def get_project_info(project_name: str):
    """Get project information by name"""
    try:
        # URL decode project name
        actual_project_name = project_name.replace('%2F', '/')
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_name)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_name}' not found"
            )
        return {
            "id": project.id,
            "name": project.name,
            "path_with_namespace": project.path_with_namespace,
            "web_url": project.web_url,
            "default_branch": project.default_branch
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project info: {str(e)}"
        )
@router.get("/projects/{project_name}/merge_requests/{mr_id}")
async def get_merge_request_info(project_name: str, mr_id: int):
    """Get merge request information"""
    try:
        # URL decode project name
        actual_project_name = project_name.replace('%2F', '/')
        # First get project
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_name)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_name}' not found"
            )
        # Then get MR
        mr_client = MergeRequestClient()
        mr = mr_client.get_merge_request(project.id, mr_id)
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merge Request {mr_id} not found in project '{actual_project_name}'"
            )
        return {
            "id": mr.id,
            "iid": mr.iid,
            "title": mr.title,
            "state": mr.state,
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "web_url": mr.web_url,
            "author": {
                "name": mr.author.name if hasattr(mr, 'author') and mr.author else None,
                "username": mr.author.username if hasattr(mr, 'author') and mr.author else None
            },
            "created_at": mr.created_at.isoformat() if hasattr(mr, 'created_at') and mr.created_at else None,
            "updated_at": mr.updated_at.isoformat() if hasattr(mr, 'updated_at') and mr.updated_at else None,
            "merged_at": mr.merged_at.isoformat() if hasattr(mr, 'merged_at') and mr.merged_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get merge request info: {str(e)}"
        )
@router.get("/projects/{project_name}/merge_requests/{mr_id}/pipelines")
async def get_merge_request_pipelines(project_name: str, mr_id: int):
    """Get pipelines for a merge request"""
    try:
        # URL decode project name
        actual_project_name = project_name.replace('%2F', '/')
        # First get project
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_name)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_name}' not found"
            )
        # Get MR to validate it exists
        mr_client = MergeRequestClient()
        mr = mr_client.get_merge_request(project.id, mr_id)
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merge Request {mr_id} not found in project '{actual_project_name}'"
            )
        # Get pipelines for the MR
        pipelines = mr_client.get_merge_request_pipelines(project.id, mr.iid)
        pipeline_list = []
        for pipeline in pipelines:
            pipeline_list.append({
                "id": pipeline.get("id"),
                "status": pipeline.get("status"),
                "ref": pipeline.get("ref"),
                "web_url": pipeline.get("web_url"),
                "created_at": pipeline.get("created_at"),
                "updated_at": pipeline.get("updated_at")
            })
        return {
            "merge_request": {
                "id": mr.id,
                "iid": mr.iid,
                "state": mr.state,
                "source_branch": mr.source_branch
            },
            "pipelines": pipeline_list
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get merge request pipelines: {str(e)}"
        )
@router.get("/projects/{project_name}/merge_requests/{mr_id}/ci_status")
async def get_merge_request_ci_status(project_name: str, mr_id: int):
    """Get comprehensive CI status for a merge request"""
    try:
        # URL decode project name
        actual_project_name = project_name.replace('%2F', '/')
        # Get project
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_name)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_name}' not found"
            )
        # Get MR
        mr_client = MergeRequestClient()
        mr = mr_client.get_merge_request(project.id, mr_id)
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merge Request {mr_id} not found in project '{actual_project_name}'"
            )
        # Get latest pipeline for this MR
        latest_pipeline = mr_client.get_latest_mr_pipeline(project.id, mr.iid)
        ci_status = {
            "merge_request": {
                "id": mr.id,
                "iid": mr.iid,
                "title": mr.title,
                "state": mr.state,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "web_url": mr.web_url
            },
            "pipeline": None,
            "jobs": [],
            "overall_status": "no_pipeline"
        }
        if latest_pipeline:
            pipeline_client = PipelineClient()
            job_client = JobClient()
            # Get pipeline details
            pipeline_details = pipeline_client.get_pipeline(project.id, latest_pipeline["id"])
            # Get jobs for this pipeline
            jobs = job_client.list_jobs(project.id, latest_pipeline["id"])
            ci_status.update({
                "pipeline": {
                    "id": pipeline_details.id,
                    "status": pipeline_details.status,
                    "ref": pipeline_details.ref,
                    "web_url": pipeline_details.web_url,
                    "created_at": getattr(pipeline_details, 'created_at', None),
                    "updated_at": getattr(pipeline_details, 'updated_at', None)
                },
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "status": job.status,
                        "stage": job.stage,
                        "started_at": job.started_at,
                        "finished_at": job.finished_at,
                        "web_url": getattr(job, 'web_url', None)
                    } for job in jobs
                ],
                "overall_status": pipeline_details.status
            })
        return ci_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CI status: {str(e)}"
        )
@router.get("/projects/{project_name}/pipelines/{pipeline_id}/jobs/{job_id}/trace")
async def get_job_trace(project_name: str, pipeline_id: int, job_id: int):
    """Get job trace/logs"""
    try:
        # URL decode project name
        actual_project_name = project_name.replace('%2F', '/')
        # Get project
        project_client = ProjectClient()
        project = project_client.get_project_by_name(actual_project_name)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{actual_project_name}' not found"
            )
        # Get job trace
        job_client = JobClient()
        trace = job_client.get_job_trace(project.id, job_id)
        return {
            "job_id": job_id,
            "pipeline_id": pipeline_id,
            "trace": trace
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job trace: {str(e)}"
        )
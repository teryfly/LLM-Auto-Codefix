import logging
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from clients.gitlab.gitlab_client import GitLabClient
from clients.gitlab.project_client import ProjectClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.gitlab.job_client import JobClient
from clients.gitlab.merge_request_client import MergeRequestClient

logger = logging.getLogger("gitlab_proxy_service")

class GitLabProxyService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.project_client = ProjectClient()
        self.pipeline_client = PipelineClient()
        self.job_client = JobClient()
        self.mr_client = MergeRequestClient()

    def get_project(self, project_path: str) -> Dict[str, Any]:
        """Get project information"""
        try:
            project = self.project_client.get_project_by_name(project_path)
            if project:
                return project.dict()
            else:
                raise ValueError(f"Project {project_path} not found")
        except Exception as e:
            logger.error(f"Failed to get project {project_path}: {e}")
            raise

    def list_pipelines(self, project_id: int, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """List pipelines for a project"""
        try:
            ref = params.get("ref") if params else None
            pipelines = self.pipeline_client.list_pipelines(project_id, ref, params)
            return [pipeline.dict() for pipeline in pipelines]
        except Exception as e:
            logger.error(f"Failed to list pipelines for project {project_id}: {e}")
            raise

    def get_pipeline(self, project_id: int, pipeline_id: int) -> Dict[str, Any]:
        """Get pipeline details"""
        try:
            pipeline = self.pipeline_client.get_pipeline(project_id, pipeline_id)
            return pipeline.dict()
        except Exception as e:
            logger.error(f"Failed to get pipeline {pipeline_id} for project {project_id}: {e}")
            raise

    def create_pipeline(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pipeline"""
        try:
            ref = data.get("ref", "main")
            pipeline = self.pipeline_client.create_pipeline(project_id, ref)
            return pipeline.dict()
        except Exception as e:
            logger.error(f"Failed to create pipeline for project {project_id}: {e}")
            raise

    def list_jobs(self, project_id: int, pipeline_id: int) -> List[Dict[str, Any]]:
        """List jobs for a pipeline"""
        try:
            jobs = self.job_client.list_jobs(project_id, pipeline_id)
            return [job.dict() for job in jobs]
        except Exception as e:
            logger.error(f"Failed to list jobs for pipeline {pipeline_id}: {e}")
            raise

    def get_job_trace(self, project_id: int, job_id: int) -> str:
        """Get job trace output"""
        try:
            trace = self.job_client.get_job_trace(project_id, job_id)
            return trace
        except Exception as e:
            logger.error(f"Failed to get trace for job {job_id}: {e}")
            raise

    def create_merge_request(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a merge request"""
        try:
            source_branch = data["source_branch"]
            target_branch = data["target_branch"]
            title = data["title"]
            mr = self.mr_client.create_merge_request(project_id, source_branch, target_branch, title)
            return mr.dict()
        except Exception as e:
            logger.error(f"Failed to create merge request for project {project_id}: {e}")
            raise

    def merge_merge_request(self, project_id: int, mr_iid: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a merge request"""
        try:
            result = self.mr_client.merge_mr(project_id, mr_iid)
            return result
        except Exception as e:
            logger.error(f"Failed to merge MR {mr_iid} for project {project_id}: {e}")
            raise
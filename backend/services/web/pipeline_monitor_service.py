import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from models.web.api_models import PipelineStatusResponse, JobStatusResponse
from services.web.gitlab_proxy_service import GitLabProxyService
from state.pipeline_state import PipelineStateManager

logger = logging.getLogger("pipeline_monitor_service")

class PipelineMonitorService:
    def __init__(self, config: AppConfig, gitlab_service: GitLabProxyService):
        self.config = config
        self.gitlab_service = gitlab_service
        self.pipeline_states = PipelineStateManager()

    def get_pipeline_status(self, session_id: str) -> PipelineStatusResponse:
        """Get current pipeline status for a session"""
        try:
            pipeline_state = self.pipeline_states.get_state(session_id)
            if not pipeline_state:
                raise ValueError(f"No pipeline state found for session {session_id}")

            # Refresh pipeline status from GitLab
            if pipeline_state.project_id and pipeline_state.pipeline_id:
                try:
                    pipeline_data = self.gitlab_service.get_pipeline(
                        pipeline_state.project_id,
                        pipeline_state.pipeline_id
                    )
                    pipeline_state.status = pipeline_data["status"]
                    pipeline_state.updated_at = datetime.utcnow()
                except Exception as e:
                    logger.warning(f"Failed to refresh pipeline status: {e}")

            return PipelineStatusResponse(
                session_id=session_id,
                pipeline_id=pipeline_state.pipeline_id,
                project_id=pipeline_state.project_id,
                status=pipeline_state.status,
                ref=pipeline_state.ref,
                sha=pipeline_state.sha,
                web_url=pipeline_state.web_url,
                created_at=pipeline_state.created_at,
                updated_at=pipeline_state.updated_at
            )
        except Exception as e:
            logger.error(f"Failed to get pipeline status for session {session_id}: {e}")
            raise

    def get_job_statuses(self, session_id: str) -> List[JobStatusResponse]:
        """Get job statuses for a session's pipeline"""
        try:
            pipeline_state = self.pipeline_states.get_state(session_id)
            if not pipeline_state or not pipeline_state.pipeline_id:
                raise ValueError(f"No pipeline found for session {session_id}")

            # Get jobs from GitLab
            jobs_data = self.gitlab_service.list_jobs(
                pipeline_state.project_id,
                pipeline_state.pipeline_id
            )

            job_responses = []
            for job_data in jobs_data:
                job_responses.append(JobStatusResponse(
                    id=job_data["id"],
                    name=job_data["name"],
                    status=job_data["status"],
                    stage=job_data.get("stage"),
                    ref=job_data.get("ref"),
                    started_at=job_data.get("started_at"),
                    finished_at=job_data.get("finished_at"),
                    web_url=job_data.get("web_url")
                ))

            return job_responses
        except Exception as e:
            logger.error(f"Failed to get job statuses for session {session_id}: {e}")
            raise

    def get_monitor_data(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive pipeline monitoring data"""
        try:
            pipeline_status = self.get_pipeline_status(session_id)
            job_statuses = self.get_job_statuses(session_id)

            # Calculate summary statistics
            total_jobs = len(job_statuses)
            completed_jobs = len([j for j in job_statuses if j.status in ["success", "failed", "canceled"]])
            failed_jobs = len([j for j in job_statuses if j.status == "failed"])

            return {
                "pipeline": pipeline_status.dict(),
                "jobs": [job.dict() for job in job_statuses],
                "summary": {
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "failed_jobs": failed_jobs,
                    "progress_percent": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get monitor data for session {session_id}: {e}")
            raise

    def retry_failed_jobs(self, session_id: str) -> Dict[str, Any]:
        """Retry failed jobs in the pipeline"""
        try:
            # This would typically involve calling GitLab API to retry jobs
            # For now, return a placeholder response
            logger.info(f"Retry failed jobs requested for session {session_id}")
            return {
                "session_id": session_id,
                "action": "retry_failed_jobs",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to retry failed jobs for session {session_id}: {e}")
            raise

    def get_job_trace(self, session_id: str, job_id: int) -> str:
        """Get trace output for a specific job"""
        try:
            pipeline_state = self.pipeline_states.get_state(session_id)
            if not pipeline_state:
                raise ValueError(f"No pipeline state found for session {session_id}")

            trace = self.gitlab_service.get_job_trace(pipeline_state.project_id, job_id)
            return trace
        except Exception as e:
            logger.error(f"Failed to get job trace for job {job_id}: {e}")
            raise

    def update_pipeline_state(self, session_id: str, project_id: int, pipeline_id: int, **kwargs):
        """Update pipeline state for a session"""
        self.pipeline_states.update_state(session_id, project_id, pipeline_id, **kwargs)
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from tasks.task_base import BaseTask
from services.web.gitlab_proxy_service import GitLabProxyService

logger = logging.getLogger("pipeline_tasks")

class PipelineMonitorTask(BaseTask):
    """Task for monitoring pipeline status"""

    def __init__(self, session_id: str, project_id: int, pipeline_id: int, gitlab_service: GitLabProxyService):
        super().__init__(f"pipeline_monitor_{session_id}_{pipeline_id}", "Pipeline Monitor")
        self.session_id = session_id
        self.project_id = project_id
        self.pipeline_id = pipeline_id
        self.gitlab_service = gitlab_service
        self.check_interval = 5  # seconds

    async def execute(self) -> Dict[str, Any]:
        """Monitor pipeline until completion"""
        try:
            self.add_log(f"Starting pipeline monitoring for pipeline {self.pipeline_id}")

            while True:
                # Get pipeline status
                pipeline_data = self.gitlab_service.get_pipeline(self.project_id, self.pipeline_id)
                status = pipeline_data["status"]

                self.add_log(f"Pipeline status: {status}")

                # Check if pipeline is completed
                if status in ["success", "failed", "canceled", "skipped"]:
                    self.add_log(f"Pipeline completed with status: {status}")

                    # Get final job statuses
                    jobs = self.gitlab_service.list_jobs(self.project_id, self.pipeline_id)

                    return {
                        "pipeline_id": self.pipeline_id,
                        "status": status,
                        "jobs": jobs,
                        "pipeline_data": pipeline_data
                    }

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        except Exception as e:
            self.add_log(f"Pipeline monitoring failed: {e}")
            raise

class JobTraceCollectorTask(BaseTask):
    """Task for collecting job traces"""

    def __init__(self, session_id: str, project_id: int, job_ids: List[int], gitlab_service: GitLabProxyService):
        super().__init__(f"job_trace_collector_{session_id}", "Job Trace Collector")
        self.session_id = session_id
        self.project_id = project_id
        self.job_ids = job_ids
        self.gitlab_service = gitlab_service

    async def execute(self) -> Dict[str, Any]:
        """Collect traces for specified jobs"""
        try:
            self.add_log(f"Collecting traces for {len(self.job_ids)} jobs")

            traces = {}
            for job_id in self.job_ids:
                try:
                    trace = self.gitlab_service.get_job_trace(self.project_id, job_id)
                    traces[job_id] = trace
                    self.add_log(f"Collected trace for job {job_id}")
                except Exception as e:
                    self.add_log(f"Failed to collect trace for job {job_id}: {e}")
                    traces[job_id] = f"Error collecting trace: {e}"

            return {"traces": traces}

        except Exception as e:
            self.add_log(f"Job trace collection failed: {e}")
            raise

class PipelineRetryTask(BaseTask):
    """Task for retrying failed pipeline jobs"""

    def __init__(self, session_id: str, project_id: int, pipeline_id: int, gitlab_service: GitLabProxyService):
        super().__init__(f"pipeline_retry_{session_id}_{pipeline_id}", "Pipeline Retry")
        self.session_id = session_id
        self.project_id = project_id
        self.pipeline_id = pipeline_id
        self.gitlab_service = gitlab_service

    async def execute(self) -> Dict[str, Any]:
        """Retry failed jobs in the pipeline"""
        try:
            self.add_log(f"Retrying failed jobs for pipeline {self.pipeline_id}")

            # Get job data
            jobs = self.gitlab_service.list_jobs(self.project_id, self.pipeline_id)
            failed_jobs = [job for job in jobs if job["status"] == "failed"]

            if not failed_jobs:
                self.add_log("No failed jobs to retry")
                return {"retried_jobs": []}

            retried_jobs = []
            for job in failed_jobs:
                try:
                    # Note: Actual job retry would require GitLab API call
                    # This is a placeholder for the retry logic
                    job_id = job["id"]
                    self.add_log(f"Retrying job {job_id}: {job['name']}")
                    retried_jobs.append(job_id)
                except Exception as e:
                    self.add_log(f"Failed to retry job {job['id']}: {e}")

            return {"retried_jobs": retried_jobs}

        except Exception as e:
            self.add_log(f"Pipeline retry failed: {e}")
            raise

class PipelineStatusAggregatorTask(BaseTask):
    """Task for aggregating pipeline and job statuses"""

    def __init__(self, session_id: str, project_id: int, pipeline_id: int, gitlab_service: GitLabProxyService):
        super().__init__(f"pipeline_aggregator_{session_id}_{pipeline_id}", "Pipeline Status Aggregator")
        self.session_id = session_id
        self.project_id = project_id
        self.pipeline_id = pipeline_id
        self.gitlab_service = gitlab_service

    async def execute(self) -> Dict[str, Any]:
        """Aggregate comprehensive pipeline status"""
        try:
            self.add_log(f"Aggregating status for pipeline {self.pipeline_id}")

            # Get pipeline data
            pipeline_data = self.gitlab_service.get_pipeline(self.project_id, self.pipeline_id)

            # Get job data
            jobs = self.gitlab_service.list_jobs(self.project_id, self.pipeline_id)

            # Calculate statistics
            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs if j["status"] in ["success", "failed", "canceled"]])
            failed_jobs = len([j for j in jobs if j["status"] == "failed"])
            running_jobs = len([j for j in jobs if j["status"] in ["running", "pending"]])

            # Group jobs by stage
            stages = {}
            for job in jobs:
                stage = job.get("stage", "unknown")
                if stage not in stages:
                    stages[stage] = []
                stages[stage].append(job)

            aggregated_data = {
                "pipeline": pipeline_data,
                "jobs": jobs,
                "stages": stages,
                "statistics": {
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "failed_jobs": failed_jobs,
                    "running_jobs": running_jobs,
                    "progress_percent": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self.add_log("Pipeline status aggregation completed")
            return aggregated_data

        except Exception as e:
            self.add_log(f"Pipeline status aggregation failed: {e}")
            raise
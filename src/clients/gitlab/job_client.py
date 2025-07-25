# clients/gitlab/job_client.py

from .gitlab_client import GitLabClient
from models.gitlab_models import GitLabJob

class JobClient(GitLabClient):
    def list_jobs(self, project_id: int, pipeline_id: int):
        jobs = self.get(f"api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs")
        return [GitLabJob(**j) for j in jobs]

    def get_job_trace(self, project_id: int, job_id: int) -> str:
        url = f"{self.base_url}/api/v4/projects/{project_id}/jobs/{job_id}/trace"
        resp = self._session().get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.text

    def _session(self):
        import requests
        return requests.Session()
# clients/gitlab/job_client.py
import requests
from .gitlab_client import GitLabClient
from models.gitlab_models import GitLabJob

class JobClient(GitLabClient):
    def list_jobs(self, project_id: int, pipeline_id: int):
        jobs = self.get(f"api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs")
        return [GitLabJob(**j) for j in jobs]

    def get_job_trace(self, project_id: int, job_id: int) -> str:
        """获取Job的日志输出"""
        try:
            url = f"{self.base_url}/api/v4/projects/{project_id}/jobs/{job_id}/trace"
            resp = requests.get(url, headers=self._headers(), timeout=30)
            if resp.status_code == 401:
                return "Unauthorized (401): Please check gitlab_private_token in your config."
            if resp.status_code == 403:
                return "Forbidden (403): Token lacks required permissions to read job traces."
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    return "Job trace not found or job has not started yet."
                elif e.response.status_code == 403:
                    return "Access denied to job trace."
            return f"Failed to fetch job trace: {str(e)}"
        except Exception as e:
            return f"Error retrieving job trace: {str(e)}"

    def get_job_details(self, project_id: int, job_id: int):
        """获取Job的详细信息"""
        try:
            job = self.get(f"api/v4/projects/{project_id}/jobs/{job_id}")
            return GitLabJob(**job)
        except Exception as e:
            raise RuntimeError(f"Failed to get job details: {str(e)}")
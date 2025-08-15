# clients/gitlab/pipeline_client.py
from .gitlab_client import GitLabClient
from models.gitlab_models import GitLabPipeline
class PipelineClient(GitLabClient):
    def create_pipeline(self, project_id: int, ref: str):
        data = {"ref": ref}
        pipeline = self.post(f"api/v4/projects/{project_id}/pipeline", data=data)
        return GitLabPipeline(**pipeline)
    def get_pipeline(self, project_id: int, pipeline_id: int):
        pipeline = self.get(f"api/v4/projects/{project_id}/pipelines/{pipeline_id}")
        return GitLabPipeline(**pipeline)
    def list_pipelines(self, project_id: int, ref: str = None, params: dict = None):
        if params is None:
            params = {}
        if ref:
            params["ref"] = ref
        pipelines = self.get(f"api/v4/projects/{project_id}/pipelines", params=params)
        return [GitLabPipeline(**p) for p in pipelines]
    def get_latest_pipeline(self, project_id: int, ref: str = None):
        """获取最新的Pipeline"""
        params = {"per_page": 1}
        if ref:
            params["ref"] = ref
        pipelines = self.get(f"api/v4/projects/{project_id}/pipelines", params=params)
        if pipelines:
            return GitLabPipeline(**pipelines[0])
        return None
    def get_pipeline_jobs(self, project_id: int, pipeline_id: int):
        """获取Pipeline下的所有Jobs"""
        jobs = self.get(f"api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs")
        return jobs
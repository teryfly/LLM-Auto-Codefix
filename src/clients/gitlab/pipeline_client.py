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

    def list_pipelines(self, project_id: int, ref: str = None):
        params = {"ref": ref} if ref else None
        pipelines = self.get(f"api/v4/projects/{project_id}/pipelines", params=params)
        return [GitLabPipeline(**p) for p in pipelines]
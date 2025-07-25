# clients/gitlab/merge_request_client.py

from .gitlab_client import GitLabClient
from models.gitlab_models import MergeRequest

class MergeRequestClient(GitLabClient):
    def create_merge_request(self, project_id: int, source_branch: str, target_branch: str, title: str):
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": False
        }
        mr = self.post(f"api/v4/projects/{project_id}/merge_requests", data=data)
        return MergeRequest(**mr)

    def get_merge_request(self, project_id: int, mr_id: int):
        mr = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_id}")
        return MergeRequest(**mr)
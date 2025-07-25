# clients/gitlab/project_client.py

from .gitlab_client import GitLabClient
from models.gitlab_models import GitLabProject

class ProjectClient(GitLabClient):
    def get_project_by_name(self, name: str):
        projects = self.get(f"api/v4/projects?search={name}")
        for p in projects:
            if p["path_with_namespace"].endswith(name):
                return GitLabProject(**p)
        return None

    def check_project_exists(self, name: str) -> bool:
        return self.get_project_by_name(name) is not None
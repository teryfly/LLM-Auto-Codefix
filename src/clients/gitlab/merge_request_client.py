# clients/gitlab/merge_request_client.py
from .gitlab_client import GitLabClient
from models.gitlab_models import MergeRequest
from config.config_manager import ConfigManager
class MergeRequestClient(GitLabClient):
    def create_merge_request(self, project_id: int, source_branch: str, target_branch: str, title: str):
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": False
        }
        mr = self.post(f"api/v4/projects/{project_id}/merge_requests", data=data)
        return MergeRequest(**mr)
    def get_merge_request(self, project_id: int, mr_id: int):
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")
        mr = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_id}")
        return MergeRequest(**mr)
    def get_merge_request_pipelines(self, project_id: int, mr_iid: int):
        """获取MR相关的所有Pipeline"""
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")
        pipelines = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}/pipelines")
        return pipelines
    def get_latest_mr_pipeline(self, project_id: int, mr_iid: int):
        """获取MR的最新Pipeline"""
        pipelines = self.get_merge_request_pipelines(project_id, mr_iid)
        if pipelines:
            return pipelines[0]  # 最新的Pipeline通常在第一个
        return None
    def merge_mr(self, project_id: int, mr_iid: int):
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")
        data = {
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": False
        }
        return self.put(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}/merge", data=data)
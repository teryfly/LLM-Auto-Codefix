# clients/gitlab/merge_request_client.py
import requests
from .gitlab_client import GitLabClient
from models.gitlab_models import MergeRequest
from config.config_manager import ConfigManager
from clients.logging.logger import logger
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
    def can_merge(self, project_id: int, mr_iid: int):
        """检查MR是否可以合并"""
        try:
            config = ConfigManager.get_config()
            http_url = getattr(config.services, "gitlab_http_url", None)
            if not http_url:
                raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
            self.base_url = http_url.rstrip("/")
            mr = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}")
            # 检查MR状态和合并能力
            merge_status = {
                "can_merge": False,
                "reason": "unknown",
                "state": mr.get("state", "unknown"),
                "merge_status": mr.get("merge_status", "unknown"),
                "has_conflicts": mr.get("has_conflicts", False),
                "work_in_progress": mr.get("work_in_progress", False)
            }
            if mr.get("state") == "merged":
                merge_status["reason"] = "already_merged"
                return merge_status
            if mr.get("state") == "closed":
                merge_status["reason"] = "closed"
                return merge_status
            if mr.get("work_in_progress", False):
                merge_status["reason"] = "work_in_progress"
                return merge_status
            if mr.get("has_conflicts", False):
                merge_status["reason"] = "has_conflicts"
                return merge_status
            # 检查是否有变化
            if mr.get("merge_status") == "cannot_be_merged":
                merge_status["reason"] = "cannot_be_merged"
                return merge_status
            # 检查源分支和目标分支是否相同
            if mr.get("source_branch") == mr.get("target_branch"):
                merge_status["reason"] = "same_branch"
                return merge_status
            # 如果通过了所有检查
            if mr.get("merge_status") in ["can_be_merged", "unchecked"]:
                merge_status["can_merge"] = True
                merge_status["reason"] = "can_merge"
            else:
                merge_status["reason"] = "no_changes"
            return merge_status
        except Exception as e:
            logger.error(f"Error checking merge status: {e}")
            return {
                "can_merge": False,
                "reason": "check_failed",
                "error": str(e)
            }
    def merge_mr(self, project_id: int, mr_iid: int):
        """合并MR，带有友好的错误处理"""
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")
        # 首先检查是否可以合并
        merge_check = self.can_merge(project_id, mr_iid)
        if not merge_check["can_merge"]:
            reason = merge_check["reason"]
            if reason == "already_merged":
                raise ValueError("Merge Request has already been merged")
            elif reason == "closed":
                raise ValueError("Merge Request is closed and cannot be merged")
            elif reason == "work_in_progress":
                raise ValueError("Merge Request is marked as Work in Progress")
            elif reason == "has_conflicts":
                raise ValueError("Merge Request has conflicts that must be resolved")
            elif reason == "cannot_be_merged":
                raise ValueError("Merge Request cannot be merged due to GitLab restrictions")
            elif reason == "same_branch":
                raise ValueError("Source and target branches are the same")
            elif reason == "no_changes":
                raise ValueError("No changes detected between source and target branches. The merge request may not have any differences to merge.")
            elif reason == "check_failed":
                error_msg = merge_check.get("error", "Unknown error")
                raise ValueError(f"Failed to check merge status: {error_msg}")
            else:
                raise ValueError(f"Merge Request cannot be merged: {reason}")
        # 如果可以合并，执行合并
        try:
            data = {
                "should_remove_source_branch": True,
                "merge_when_pipeline_succeeds": False
            }
            result = self.put(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}/merge", data=data)
            logger.info(f"Successfully merged MR {mr_iid}")
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 405:
                raise ValueError("Merge not allowed: No changes detected or merge conditions not met")
            elif e.response.status_code == 409:
                raise ValueError("Merge conflict: The merge request has conflicts that must be resolved")
            elif e.response.status_code == 422:
                raise ValueError("Merge validation failed: The merge request cannot be merged")
            else:
                raise ValueError(f"Merge failed with HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error during merge: {e}")
            raise ValueError(f"Merge failed due to unexpected error: {str(e)}")
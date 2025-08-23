# clients/gitlab/merge_request_client.py
import requests
import re
from .gitlab_client import GitLabClient
from models.gitlab_models import MergeRequest
from config.config_manager import ConfigManager
from clients.logging.logger import logger

class MergeRequestClient(GitLabClient):
    def _ensure_http_base(self):
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        self.base_url = http_url.rstrip("/")

    def create_merge_request(self, project_id: int, source_branch: str, target_branch: str, title: str):
        self._ensure_http_base()
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": False
        }
        try:
            mr = self.post(f"api/v4/projects/{project_id}/merge_requests", data=data)
            return MergeRequest(**mr)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 409:
                # 解析错误消息中的 MR ID
                error_text = e.response.text
                logger.warning(f"Merge request creation failed with 409 conflict: {error_text}")
                
                existing_mr_id = self._extract_existing_mr_id(error_text)
                if existing_mr_id:
                    logger.info(f"Found existing open MR with ID: {existing_mr_id}")
                    print(f"🔍 发现已存在的开放 MR，ID: {existing_mr_id}", flush=True)
                    
                    # 尝试关闭现有的 MR
                    if self._close_existing_mr(project_id, existing_mr_id, source_branch):
                        logger.info(f"Successfully closed existing MR {existing_mr_id}, retrying creation")
                        print(f"✅ 成功关闭现有 MR {existing_mr_id}，重新创建", flush=True)
                        
                        # 重新尝试创建 MR
                        mr = self.post(f"api/v4/projects/{project_id}/merge_requests", data=data)
                        return MergeRequest(**mr)
                    else:
                        logger.error(f"Failed to close existing MR {existing_mr_id}")
                        print(f"❌ 关闭现有 MR {existing_mr_id} 失败", flush=True)
                        raise
                else:
                    logger.error("Could not extract MR ID from error message")
                    print("❌ 无法从错误消息中提取 MR ID", flush=True)
                    raise
            else:
                raise

    def _extract_existing_mr_id(self, error_text: str) -> int:
        """
        从 GitLab API 错误消息中提取现有 MR 的 ID
        错误消息格式通常为: "Another open merge request already exists for this source branch: !21"
        """
        try:
            # 使用正则表达式匹配 MR ID
            # 匹配模式: !数字 或者 #数字
            pattern = r'[!#](\d+)'
            matches = re.findall(pattern, error_text)
            
            if matches:
                mr_id = int(matches[0])
                logger.debug(f"Extracted MR ID from error message: {mr_id}")
                return mr_id
            
            # 备用匹配模式，直接查找数字
            pattern2 = r'merge request.*?(\d+)'
            matches2 = re.findall(pattern2, error_text, re.IGNORECASE)
            if matches2:
                mr_id = int(matches2[0])
                logger.debug(f"Extracted MR ID using backup pattern: {mr_id}")
                return mr_id
                
            logger.warning(f"Could not extract MR ID from error message: {error_text}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting MR ID from error message: {e}")
            return None

    def _close_existing_mr(self, project_id: int, mr_iid: int, expected_source_branch: str) -> bool:
        """
        关闭指定的 MR
        
        Args:
            project_id: 项目 ID
            mr_iid: MR 的 IID (internal ID)
            expected_source_branch: 期望的源分支名称，用于验证
            
        Returns:
            bool: 是否成功关闭
        """
        try:
            # 首先获取 MR 详情进行验证
            logger.info(f"Getting details for MR {mr_iid} to verify before closing")
            mr_details = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}")
            
            # 验证源分支是否匹配
            actual_source_branch = mr_details.get("source_branch")
            if actual_source_branch != expected_source_branch:
                logger.warning(f"MR {mr_iid} source branch mismatch. Expected: {expected_source_branch}, Actual: {actual_source_branch}")
                print(f"⚠️ MR {mr_iid} 源分支不匹配，跳过关闭", flush=True)
                return False
            
            # 检查 MR 状态
            mr_state = mr_details.get("state")
            if mr_state != "opened":
                logger.info(f"MR {mr_iid} is not in 'opened' state (current: {mr_state}), skipping close")
                print(f"ℹ️ MR {mr_iid} 状态为 {mr_state}，无需关闭", flush=True)
                return True  # 不是开放状态，认为成功
            
            logger.info(f"Closing MR {mr_iid} (source: {actual_source_branch}, title: {mr_details.get('title', 'N/A')})")
            print(f"🔒 关闭 MR {mr_iid}: {mr_details.get('title', 'N/A')}", flush=True)
            
            # 关闭 MR
            close_data = {
                "state_event": "close"
            }
            
            result = self.put(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}", data=close_data)
            
            final_state = result.get("state")
            if final_state == "closed":
                logger.info(f"Successfully closed MR {mr_iid}")
                print(f"✅ 成功关闭 MR {mr_iid}", flush=True)
                return True
            else:
                logger.error(f"Failed to close MR {mr_iid}, final state: {final_state}")
                print(f"❌ 关闭 MR {mr_iid} 失败，最终状态: {final_state}", flush=True)
                return False
                
        except Exception as e:
            logger.error(f"Error closing MR {mr_iid}: {e}")
            print(f"❌ 关闭 MR {mr_iid} 时出错: {e}", flush=True)
            return False

    def close_merge_request(self, project_id: int, mr_iid: int) -> bool:
        """
        公共方法：关闭指定的 MR
        
        Args:
            project_id: 项目 ID
            mr_iid: MR 的 IID
            
        Returns:
            bool: 是否成功关闭
        """
        self._ensure_http_base()
        return self._close_existing_mr(project_id, mr_iid, None)

    def list_open_merge_requests(self, project_id: int, source_branch: str = None) -> list:
        """
        列出项目的开放 MR
        
        Args:
            project_id: 项目 ID
            source_branch: 可选的源分支过滤
            
        Returns:
            list: MR 列表
        """
        self._ensure_http_base()
        try:
            params = {
                "state": "opened",
                "per_page": 100
            }
            if source_branch:
                params["source_branch"] = source_branch
                
            mrs = self.get(f"api/v4/projects/{project_id}/merge_requests", params=params)
            logger.info(f"Found {len(mrs)} open merge requests")
            return [MergeRequest(**mr) for mr in mrs]
            
        except Exception as e:
            logger.error(f"Error listing open merge requests: {e}")
            return []

    def get_merge_request(self, project_id: int, mr_id: int):
        self._ensure_http_base()
        mr = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_id}")
        return MergeRequest(**mr)

    def get_merge_request_pipelines(self, project_id: int, mr_iid: int):
        """获取MR相关的所有Pipeline"""
        self._ensure_http_base()
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
            self._ensure_http_base()
            mr = self.get(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}")
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
            if mr.get("merge_status") == "cannot_be_merged":
                merge_status["reason"] = "cannot_be_merged"
                return merge_status
            if mr.get("source_branch") == mr.get("target_branch"):
                merge_status["reason"] = "same_branch"
                return merge_status
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
        self._ensure_http_base()
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
        try:
            data = {
                "should_remove_source_branch": True,
                "merge_when_pipeline_succeeds": False
            }
            result = self.put(f"api/v4/projects/{project_id}/merge_requests/{mr_iid}/merge", data=data)
            logger.info(f"Successfully merged MR {mr_iid}")
            return result
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                if e.response.status_code == 405:
                    raise ValueError("Merge not allowed: No changes detected or merge conditions not met")
                elif e.response.status_code == 409:
                    raise ValueError("Merge conflict: The merge request has conflicts that must be resolved")
                elif e.response.status_code == 422:
                    raise ValueError("Merge validation failed: The merge request cannot be merged")
            raise ValueError(f"Merge failed with HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during merge: {e}")
            raise ValueError(f"Merge failed due to unexpected error: {str(e)}")
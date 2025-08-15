# controller/repo_sync_controller.py
import os
import subprocess
import shutil
from clients.logging.logger import logger
class RepoSyncController:
    def __init__(self, config):
        self.config = config
    def sync_repo(self, project_name):
        repo_url = f"{self.config.services.gitlab_url.rstrip('/')}/{project_name}.git"
        local_dir = os.path.join(self.config.paths.git_work_dir, project_name.replace("/", "_"))
        # 如果目录已存在，先删除
        if os.path.exists(local_dir):
            logger.info(f"Directory {local_dir} already exists, removing it...")
            try:
                shutil.rmtree(local_dir)
                logger.info(f"Successfully removed existing directory: {local_dir}")
            except Exception as e:
                logger.error(f"Failed to remove existing directory {local_dir}: {e}")
                raise RuntimeError(f"Failed to remove existing directory: {e}")
        # 确保父目录存在
        parent_dir = os.path.dirname(local_dir)
        os.makedirs(parent_dir, exist_ok=True)
        # 克隆仓库
        logger.info(f"Cloning repo: {repo_url} to {local_dir}")
        try:
            subprocess.run(["git", "clone", repo_url, local_dir], check=True, timeout=300)
            logger.info(f"Successfully cloned repository to {local_dir}")
        except subprocess.TimeoutExpired:
            logger.error("Git clone operation timed out")
            raise RuntimeError("Git clone operation timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e}")
            raise RuntimeError(f"Git clone failed: {e}")
        # 切换到ai分支，没有则创建
        try:
            subprocess.run(["git", "checkout", "-B", "ai"], cwd=local_dir, check=True)
            logger.info("Successfully checked out 'ai' branch")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to checkout 'ai' branch: {e}")
            # 如果checkout失败，尝试从远程拉取ai分支
            try:
                subprocess.run(["git", "fetch", "origin"], cwd=local_dir, check=True)
                subprocess.run(["git", "checkout", "-B", "ai", "origin/ai"], cwd=local_dir, check=True)
                logger.info("Successfully checked out 'ai' branch from remote")
            except subprocess.CalledProcessError as e2:
                logger.info(f"Remote 'ai' branch doesn't exist, creating new one: {e2}")
                # 如果远程也没有ai分支，创建新的
                subprocess.run(["git", "checkout", "-B", "ai"], cwd=local_dir, check=True)
        # 设置本地ai分支与远程ai分支关联（如果远程存在）
        try:
            subprocess.run(["git", "branch", "--set-upstream-to=origin/ai", "ai"], cwd=local_dir, check=False)
            logger.info("Set upstream for 'ai' branch")
        except Exception as e:
            logger.info(f"Could not set upstream for 'ai' branch (this is normal for new branches): {e}")
        # 尝试拉取远程ai分支（如果存在）
        try:
            subprocess.run(["git", "pull", "origin", "ai"], cwd=local_dir, check=False)
            logger.info("Successfully pulled from remote 'ai' branch")
        except Exception as e:
            logger.info(f"Could not pull from remote 'ai' branch (this is normal for new branches): {e}")
        return local_dir
# controller/repo_sync_controller.py

import os
import subprocess
from clients.logging.logger import logger

class RepoSyncController:
    def __init__(self, config):
        self.config = config

    def sync_repo(self, project_name):
        repo_url = f"{self.config.services.gitlab_url.rstrip('/')}/{project_name}.git"
        local_dir = os.path.join(self.config.paths.git_work_dir, project_name.replace("/", "_"))
        if not os.path.exists(local_dir):
            logger.info(f"Cloning repo: {repo_url} to {local_dir}")
            subprocess.run(["git", "clone", repo_url, local_dir], check=True)
        else:
            logger.info(f"Pulling latest for repo in {local_dir}")
            # 切换到ai分支，没有则创建
            subprocess.run(["git", "checkout", "-B", "ai"], cwd=local_dir, check=True)
            # 设置本地ai分支与远程ai分支关联，若未设置
            subprocess.run(["git", "branch", "--set-upstream-to=origin/ai", "ai"], cwd=local_dir, check=False)
            # 拉取远程ai分支
            subprocess.run(["git", "pull", "origin", "ai"], cwd=local_dir, check=True)
        return local_dir
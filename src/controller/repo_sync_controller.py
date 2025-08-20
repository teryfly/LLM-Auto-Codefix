# controller/repo_sync_controller.py
import os
import subprocess
from clients.logging.logger import logger
class RepoSyncController:
    def __init__(self, config):
        self.config = config
    def _run(self, cmd, cwd, allow_fail=False):
        """运行git命令并捕获错误"""
        try:
            subprocess.run(cmd, cwd=cwd, check=True, timeout=300)
            return True
        except subprocess.CalledProcessError as e:
            if allow_fail:
                logger.warning(f"Command {cmd} failed but ignored: {e}")
                return False
            raise
    def sync_repo(self, project_name):
        repo_url = f"{self.config.services.gitlab_url.rstrip('/')}/{project_name}.git"
        local_dir = os.path.join(self.config.paths.git_work_dir, project_name.replace("/", "_"))
        if os.path.exists(local_dir):
            logger.info(f"Directory {local_dir} already exists, will reuse it instead of deleting.")
            try:
                # 确保fetch最新远程
                self._run(["git", "fetch", "--all"], cwd=local_dir)
                # 强制重置到远程 main 分支，避免 checkout 冲突
                self._run(["git", "reset", "--hard", "origin/main"], cwd=local_dir)
                logger.info("Reset local repo to origin/main")
                # 切换到 main 分支（如果不存在则创建）
                self._run(["git", "checkout", "-B", "main", "origin/main"], cwd=local_dir)
                logger.info("Checked out to 'main' branch")
                # 清理未跟踪文件和冲突状态
                self._run(["git", "clean", "-fd"], cwd=local_dir)
                self._run(["git", "reset", "--hard"], cwd=local_dir)
                logger.info("Cleaned untracked files and reset any conflicts")
                # 拉取远程更新
                self._run(["git", "pull"], cwd=local_dir, allow_fail=True)
                logger.info("Pulled latest changes from remote")
            except Exception as e:
                logger.error(f"Failed to update existing repo at {local_dir}: {e}")
                raise RuntimeError(f"Failed to update existing repo: {e}")
        else:
            # 确保父目录存在
            parent_dir = os.path.dirname(local_dir)
            os.makedirs(parent_dir, exist_ok=True)
            logger.info(f"Cloning repo: {repo_url} to {local_dir}")
            try:
                self._run(["git", "clone", repo_url, local_dir], cwd=None)
                logger.info(f"Successfully cloned repository to {local_dir}")
            except Exception as e:
                logger.error(f"Git clone failed: {e}")
                raise RuntimeError(f"Git clone failed: {e}")
        # 切换到 ai 分支，使用强制重置避免冲突
        try:
            # 先尝试获取远程 ai 分支
            self._run(["git", "fetch", "origin", "ai"], cwd=local_dir, allow_fail=True)
            # 如果远程有 ai 分支，则重置到远程状态
            if self._run(["git", "rev-parse", "--verify", "origin/ai"], cwd=local_dir, allow_fail=True):
                self._run(["git", "checkout", "-B", "ai", "origin/ai"], cwd=local_dir)
                logger.info("Reset ai branch to origin/ai")
            else:
                # 如果远程没有 ai 分支，则从当前 main 创建新的
                self._run(["git", "checkout", "-b", "ai"], cwd=local_dir)
                logger.info("Created new ai branch from main")
            # 再次确保没有冲突状态
            self._run(["git", "reset", "--hard"], cwd=local_dir)
        except Exception as e:
            logger.error(f"Failed to setup ai branch: {e}")
            raise RuntimeError(f"Failed to setup ai branch: {e}")
        return local_dir
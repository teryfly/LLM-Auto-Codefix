# operations/git/git_manager.py
from .git_commands import (
    clone_repository,
    checkout_branch,
    create_branch,
    pull,
    push_to_ai_branch,
    add_all_and_commit,
)
from .git_validator import (
    is_git_repository,
    is_branch_exists,
    is_clean_working_directory,
)
import os
import shutil
from clients.logging.logger import logger
class GitManager:
    def __init__(self, repo_url: str, work_dir: str):
        self.repo_url = repo_url  # 必须为 SSH 地址
        self.work_dir = work_dir
    def ensure_repository(self, force_clean: bool = True):
        """
        确保仓库存在并且是最新的
        Args:
            force_clean: 如果为True，会删除现有目录重新克隆；如果为False，会尝试更新现有仓库
        """
        if force_clean and os.path.exists(self.work_dir):
            logger.info(f"Force clean enabled, removing existing directory: {self.work_dir}")
            try:
                shutil.rmtree(self.work_dir)
                logger.info(f"Successfully removed existing directory: {self.work_dir}")
            except Exception as e:
                logger.error(f"Failed to remove existing directory: {e}")
                raise RuntimeError(f"Failed to remove existing directory: {e}")
        if not os.path.exists(self.work_dir) or not is_git_repository(self.work_dir):
            # 确保父目录存在
            parent_dir = os.path.dirname(self.work_dir)
            os.makedirs(parent_dir, exist_ok=True)
            # 仅用 SSH 地址 clone
            logger.info(f"Cloning repository from {self.repo_url} to {self.work_dir}")
            clone_repository(self.repo_url, self.work_dir)
        else:
            logger.info(f"Repository already exists at {self.work_dir}, pulling latest changes")
            try:
                pull(self.work_dir)
            except Exception as e:
                logger.warning(f"Failed to pull latest changes: {e}")
                if force_clean:
                    logger.info("Pull failed, removing directory and re-cloning...")
                    shutil.rmtree(self.work_dir)
                    parent_dir = os.path.dirname(self.work_dir)
                    os.makedirs(parent_dir, exist_ok=True)
                    clone_repository(self.repo_url, self.work_dir)
                else:
                    raise
    def create_and_checkout_branch(self, branch_name: str):
        """
        创建并切换到指定分支，如果分支已存在则直接切换
        """
        try:
            if not is_branch_exists(branch_name, self.work_dir):
                logger.info(f"Creating new branch: {branch_name}")
                create_branch(branch_name, self.work_dir)
            else:
                logger.info(f"Branch {branch_name} already exists, checking out")
                checkout_branch(branch_name, self.work_dir)
        except Exception as e:
            logger.error(f"Failed to create/checkout branch {branch_name}: {e}")
            # 尝试强制创建分支
            try:
                logger.info(f"Attempting to force create branch: {branch_name}")
                from .git_commands import run_git_command
                run_git_command(["checkout", "-B", branch_name], cwd=self.work_dir, capture_output=False)
                logger.info(f"Successfully force created branch: {branch_name}")
            except Exception as e2:
                logger.error(f"Failed to force create branch: {e2}")
                raise RuntimeError(f"Failed to create/checkout branch {branch_name}: {e2}")
    def sync_and_commit(self, message: str):
        """
        同步更改并提交
        """
        try:
            if not is_clean_working_directory(self.work_dir):
                logger.info(f"Working directory has changes, committing with message: {message}")
                add_all_and_commit(message, self.work_dir)
                return True
            else:
                logger.info("Working directory is clean, no changes to commit")
                return False
        except Exception as e:
            logger.error(f"Failed to sync and commit: {e}")
            raise RuntimeError(f"Failed to sync and commit: {e}")
    def push_to_ai(self):
        """
        推送到ai分支
        """
        try:
            logger.info("Pushing changes to 'ai' branch")
            push_to_ai_branch(self.work_dir)
            logger.info("Successfully pushed to 'ai' branch")
        except Exception as e:
            logger.error(f"Failed to push to 'ai' branch: {e}")
            raise RuntimeError(f"Failed to push to 'ai' branch: {e}")
    def cleanup_directory(self):
        """
        清理工作目录
        """
        if os.path.exists(self.work_dir):
            try:
                logger.info(f"Cleaning up directory: {self.work_dir}")
                shutil.rmtree(self.work_dir)
                logger.info(f"Successfully cleaned up directory: {self.work_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup directory: {e}")
                raise RuntimeError(f"Failed to cleanup directory: {e}")
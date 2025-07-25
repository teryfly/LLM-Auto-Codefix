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

class GitManager:
    def __init__(self, repo_url: str, work_dir: str):
        self.repo_url = repo_url  # 必须为 SSH 地址
        self.work_dir = work_dir

    def ensure_repository(self):
        if not os.path.exists(self.work_dir) or not is_git_repository(self.work_dir):
            # 仅用 SSH 地址 clone
            clone_repository(self.repo_url, self.work_dir)
        else:
            pull(self.work_dir)

    def create_and_checkout_branch(self, branch_name: str):
        if not is_branch_exists(branch_name, self.work_dir):
            create_branch(branch_name, self.work_dir)
        else:
            checkout_branch(branch_name, self.work_dir)

    def sync_and_commit(self, message: str):
        if not is_clean_working_directory(self.work_dir):
            add_all_and_commit(message, self.work_dir)
            return True
        return False

    def push_to_ai(self):
        push_to_ai_branch(self.work_dir)
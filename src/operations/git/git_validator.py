# operations/git/git_validator.py

import os

def is_git_repository(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))

def is_branch_exists(branch: str, cwd: str) -> bool:
    """Check if a branch exists in the local repo."""
    from .git_commands import run_git_command
    result = run_git_command(["branch", "--list", branch], cwd=cwd)
    return bool(result.stdout.strip())

def is_clean_working_directory(cwd: str) -> bool:
    from .git_commands import run_git_command
    result = run_git_command(["status", "--porcelain"], cwd=cwd)
    return result.stdout.strip() == ""
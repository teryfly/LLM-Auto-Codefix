# operations/git/git_commands.py

import subprocess
from typing import List, Optional

def run_git_command(args: List[str], cwd: Optional[str] = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in a subprocess."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture_output,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
    return result

def clone_repository(repo_url: str, dest_dir: str) -> None:
    run_git_command(["clone", repo_url, dest_dir], capture_output=False)

def checkout_branch(branch: str, cwd: str) -> None:
    run_git_command(["checkout", branch], cwd=cwd, capture_output=False)

def create_branch(branch: str, cwd: str) -> None:
    run_git_command(["checkout", "-b", branch], cwd=cwd, capture_output=False)

def pull(cwd: str) -> None:
    run_git_command(["pull"], cwd=cwd, capture_output=False)

def push_to_ai_branch(cwd: str) -> None:
    run_git_command(["push", "origin", "HEAD:ai"], cwd=cwd, capture_output=False)

def add_all_and_commit(message: str, cwd: str) -> None:
    run_git_command(["add", "."], cwd=cwd, capture_output=False)
    run_git_command(["commit", "-m", message], cwd=cwd, capture_output=False)
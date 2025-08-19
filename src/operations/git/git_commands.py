# operations/git/git_commands.py
import subprocess
import os
import shutil
from typing import List, Optional
from clients.logging.logger import logger
import sys

def run_git_command(args: List[str], cwd: Optional[str] = None, capture_output: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a git command in a subprocess with timeout and error handling."""
    cmd = ["git"] + args
    try:
        logger.debug(f"Running git command: {' '.join(cmd)} in {cwd or 'current directory'}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            stderr=subprocess.STDOUT  # 将stderr重定向到stdout，确保捕获所有输出
        )
        
        # 记录命令输出（包括错误输出）
        if result.stdout:
            logger.info(f"Git command output: {result.stdout}")
            # 同时输出到控制台，确保workflow executor能捕获
            print(f"Git output: {result.stdout}", flush=True)
        
        if result.returncode != 0:
            error_msg = f"Git command failed: {' '.join(cmd)}\nReturn code: {result.returncode}\nOutput: {result.stdout}"
            logger.error(error_msg)
            # 输出到控制台确保被捕获
            print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
            raise RuntimeError(error_msg)
            
        logger.debug(f"Git command succeeded: {' '.join(cmd)}")
        return result
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Git command timed out after {timeout}s: {' '.join(cmd)}"
        logger.error(error_msg)
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Git command failed with exception: {' '.join(cmd)}\nError: {str(e)}"
        logger.error(error_msg)
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def clone_repository(repo_url: str, dest_dir: str, timeout: int = 300) -> None:
    """Clone a repository with proper error handling and cleanup."""
    # 确保目标目录不存在或为空
    if os.path.exists(dest_dir):
        if os.path.isdir(dest_dir) and os.listdir(dest_dir):
            logger.warning(f"Destination directory {dest_dir} is not empty, removing it")
            shutil.rmtree(dest_dir)
        elif os.path.isfile(dest_dir):
            logger.warning(f"Destination {dest_dir} is a file, removing it")
            os.remove(dest_dir)

    # 确保父目录存在
    parent_dir = os.path.dirname(dest_dir)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    try:
        logger.info(f"Cloning repository {repo_url} to {dest_dir}")
        print(f"Cloning repository {repo_url} to {dest_dir}", flush=True)
        
        # 使用更详细的错误处理进行clone
        result = subprocess.run(
            ["git", "clone", repo_url, dest_dir],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # 记录所有输出
        if result.stdout:
            logger.info(f"Git clone stdout: {result.stdout}")
            print(f"Git clone output: {result.stdout}", flush=True)
            
        if result.stderr:
            logger.info(f"Git clone stderr: {result.stderr}")
            print(f"Git clone error: {result.stderr}", flush=True)
            
        if result.returncode != 0:
            error_msg = f"Git clone failed with return code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
            logger.error(error_msg)
            print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
            raise RuntimeError(error_msg)
            
        logger.info(f"Successfully cloned repository to {dest_dir}")
        print(f"Successfully cloned repository to {dest_dir}", flush=True)
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Git clone timed out after {timeout}s"
        logger.error(error_msg)
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        # 如果克隆失败，清理可能创建的目录
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
                logger.info(f"Cleaned up failed clone directory: {dest_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup directory after failed clone: {cleanup_error}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Failed to clone repository: {e}"
        logger.error(error_msg)
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        # 如果克隆失败，清理可能创建的目录
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
                logger.info(f"Cleaned up failed clone directory: {dest_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup directory after failed clone: {cleanup_error}")
        raise RuntimeError(error_msg)

def checkout_branch(branch: str, cwd: str) -> None:
    """Checkout a branch with error handling."""
    try:
        logger.info(f"Checking out branch: {branch}")
        print(f"Checking out branch: {branch}", flush=True)
        run_git_command(["checkout", branch], cwd=cwd, capture_output=False)
        logger.info(f"Successfully checked out branch: {branch}")
        print(f"Successfully checked out branch: {branch}", flush=True)
    except Exception as e:
        error_msg = f"Failed to checkout branch {branch}: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def create_branch(branch: str, cwd: str) -> None:
    """Create and checkout a new branch."""
    try:
        logger.info(f"Creating and checking out new branch: {branch}")
        print(f"Creating and checking out new branch: {branch}", flush=True)
        run_git_command(["checkout", "-b", branch], cwd=cwd, capture_output=False)
        logger.info(f"Successfully created and checked out branch: {branch}")
        print(f"Successfully created and checked out branch: {branch}", flush=True)
    except Exception as e:
        error_msg = f"Failed to create branch {branch}: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def force_create_branch(branch: str, cwd: str) -> None:
    """Force create and checkout a branch (overwrites existing)."""
    try:
        logger.info(f"Force creating and checking out branch: {branch}")
        print(f"Force creating and checking out branch: {branch}", flush=True)
        run_git_command(["checkout", "-B", branch], cwd=cwd, capture_output=False)
        logger.info(f"Successfully force created and checked out branch: {branch}")
        print(f"Successfully force created and checked out branch: {branch}", flush=True)
    except Exception as e:
        error_msg = f"Failed to force create branch {branch}: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def pull(cwd: str, remote: str = "origin", branch: str = None) -> None:
    """Pull changes from remote repository."""
    try:
        if branch:
            logger.info(f"Pulling from {remote}/{branch}")
            print(f"Pulling from {remote}/{branch}", flush=True)
            run_git_command(["pull", remote, branch], cwd=cwd, capture_output=False)
        else:
            logger.info(f"Pulling from {remote}")
            print(f"Pulling from {remote}", flush=True)
            run_git_command(["pull", remote], cwd=cwd, capture_output=False)
        logger.info("Successfully pulled changes")
        print("Successfully pulled changes", flush=True)
    except Exception as e:
        error_msg = f"Failed to pull changes: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def fetch(cwd: str, remote: str = "origin") -> None:
    """Fetch changes from remote repository."""
    try:
        logger.info(f"Fetching from {remote}")
        print(f"Fetching from {remote}", flush=True)
        run_git_command(["fetch", remote], cwd=cwd, capture_output=False)
        logger.info("Successfully fetched changes")
        print("Successfully fetched changes", flush=True)
    except Exception as e:
        error_msg = f"Failed to fetch changes: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def push_to_ai_branch(cwd: str) -> None:
    """Push current branch to remote ai branch."""
    try:
        logger.info("Pushing to remote 'ai' branch")
        print("Pushing to remote 'ai' branch", flush=True)
        run_git_command(["push", "origin", "HEAD:ai"], cwd=cwd, capture_output=False)
        logger.info("Successfully pushed to remote 'ai' branch")
        print("Successfully pushed to remote 'ai' branch", flush=True)
    except Exception as e:
        error_msg = f"Failed to push to ai branch: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def add_all_and_commit(message: str, cwd: str) -> None:
    """Add all changes and commit with message."""
    try:
        logger.info("Adding all changes")
        print("Adding all changes", flush=True)
        run_git_command(["add", "."], cwd=cwd, capture_output=False)
        logger.info(f"Committing with message: {message}")
        print(f"Committing with message: {message}", flush=True)
        run_git_command(["commit", "-m", message], cwd=cwd, capture_output=False)
        logger.info("Successfully committed changes")
        print("Successfully committed changes", flush=True)
    except Exception as e:
        # 检查是否是因为没有变更而失败
        if "nothing to commit" in str(e).lower():
            logger.info("No changes to commit")
            print("No changes to commit", flush=True)
            return
        error_msg = f"Failed to add and commit changes: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def set_upstream(branch: str, remote: str, remote_branch: str, cwd: str) -> None:
    """Set upstream branch for current branch."""
    try:
        logger.info(f"Setting upstream {remote}/{remote_branch} for branch {branch}")
        print(f"Setting upstream {remote}/{remote_branch} for branch {branch}", flush=True)
        run_git_command(["branch", f"--set-upstream-to={remote}/{remote_branch}", branch], cwd=cwd)
        logger.info(f"Successfully set upstream for branch {branch}")
        print(f"Successfully set upstream for branch {branch}", flush=True)
    except Exception as e:
        logger.warning(f"Failed to set upstream (this may be normal for new branches): {e}")
        print(f"Warning: Failed to set upstream (this may be normal for new branches): {e}", flush=True)

def get_current_branch(cwd: str) -> str:
    """Get current branch name."""
    try:
        result = run_git_command(["branch", "--show-current"], cwd=cwd)
        branch = result.stdout.strip()
        logger.debug(f"Current branch: {branch}")
        return branch
    except Exception as e:
        error_msg = f"Failed to get current branch: {e}"
        print(f"fatal: {error_msg}", file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)

def branch_exists_local(branch: str, cwd: str) -> bool:
    """Check if branch exists locally."""
    try:
        result = run_git_command(["branch", "--list", branch], cwd=cwd)
        exists = bool(result.stdout.strip())
        logger.debug(f"Local branch {branch} exists: {exists}")
        return exists
    except Exception as e:
        logger.warning(f"Failed to check if local branch exists: {e}")
        return False

def branch_exists_remote(branch: str, remote: str, cwd: str) -> bool:
    """Check if branch exists on remote."""
    try:
        result = run_git_command(["branch", "-r", "--list", f"{remote}/{branch}"], cwd=cwd)
        exists = bool(result.stdout.strip())
        logger.debug(f"Remote branch {remote}/{branch} exists: {exists}")
        return exists
    except Exception as e:
        logger.warning(f"Failed to check if remote branch exists: {e}")
        return False
# controller/main_workflow/step_preparation_phase.py

import os
import subprocess
from clients.logging.logger import logger
from config.config_models import AppConfig
from typing import Dict, Any

def check_git_work_dir_exists(config: AppConfig) -> Dict[str, Any]:
    """
    检查 git_work_dir 是否存在
    
    Args:
        config: 应用配置对象
        
    Returns:
        Dict[str, Any]: 检查结果
    """
    git_work_dir = config.paths.git_work_dir
    
    logger.info(f"检查 git_work_dir 是否存在: {git_work_dir}")
    print(f"🔍 检查工作目录: {git_work_dir}", flush=True)
    
    if not os.path.exists(git_work_dir):
        error_msg = f"工作目录不存在: {git_work_dir}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        print("💡 请先创建项目目录", flush=True)
        return {
            "status": "error",
            "message": "请先创建项目",
            "path": git_work_dir
        }
    
    if not os.path.isdir(git_work_dir):
        error_msg = f"路径存在但不是目录: {git_work_dir}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": "路径不是有效目录",
            "path": git_work_dir
        }
    
    logger.info(f"工作目录存在: {git_work_dir}")
    print(f"✅ 工作目录存在: {git_work_dir}", flush=True)
    
    return {
        "status": "success",
        "message": "工作目录检查通过",
        "path": git_work_dir
    }

def check_current_git_branch(git_work_dir: str) -> Dict[str, Any]:
    """
    检查当前 git 分支
    
    Args:
        git_work_dir: git 工作目录路径
        
    Returns:
        Dict[str, Any]: 分支检查结果
    """
    logger.info("检查当前 git 分支")
    print("🌿 检查当前 git 分支", flush=True)
    
    try:
        # 检查是否是 git 仓库
        if not os.path.exists(os.path.join(git_work_dir, '.git')):
            error_msg = f"目录不是 git 仓库: {git_work_dir}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": "不是 git 仓库",
                "path": git_work_dir
            }
        
        # 获取当前分支
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            error_msg = f"获取当前分支失败: {result.stderr}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": "获取分支失败",
                "error": result.stderr
            }
        
        current_branch = result.stdout.strip()
        if not current_branch:
            current_branch = "HEAD (detached)"
        
        logger.info(f"当前分支: {current_branch}")
        print(f"🌿 当前分支: {current_branch}", flush=True)
        
        return {
            "status": "success",
            "message": "分支检查完成",
            "branch": current_branch
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "git 命令超时"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"检查分支时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

def git_add_and_show_changes(git_work_dir: str) -> Dict[str, Any]:
    """
    执行 git add . 并显示变更内容
    
    Args:
        git_work_dir: git 工作目录路径
        
    Returns:
        Dict[str, Any]: 添加结果
    """
    logger.info("执行 git add . 并显示变更")
    print("📝 添加所有变更到暂存区", flush=True)
    
    try:
        # 执行 git add .
        add_result = subprocess.run(
            ["git", "add", "."],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if add_result.returncode != 0:
            error_msg = f"git add 失败: {add_result.stderr}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": "git add 失败",
                "error": add_result.stderr
            }
        
        print("✅ git add . 完成", flush=True)
        
        # 显示暂存区变更
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if status_result.returncode != 0:
            logger.warning(f"获取 git status 失败: {status_result.stderr}")
            print(f"⚠️ 获取状态失败: {status_result.stderr}", flush=True)
        else:
            changes = status_result.stdout.strip()
            if changes:
                print("📋 变更内容:", flush=True)
                print("=" * 50, flush=True)
                print(changes, flush=True)
                print("=" * 50, flush=True)
                logger.info(f"变更内容: {changes}")
            else:
                print("ℹ️ 没有检测到变更", flush=True)
                logger.info("没有检测到变更")
        
        return {
            "status": "success",
            "message": "git add 完成",
            "changes": status_result.stdout.strip() if status_result.returncode == 0 else ""
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "git add 命令超时"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"git add 时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

def git_commit_with_note(git_work_dir: str, note: str) -> Dict[str, Any]:
    """
    使用指定备注提交变更
    
    Args:
        git_work_dir: git 工作目录路径
        note: 提交备注
        
    Returns:
        Dict[str, Any]: 提交结果
    """
    logger.info(f"提交变更，备注: {note}")
    print(f"💾 提交变更: {note}", flush=True)
    
    try:
        # 执行 git commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", note],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if commit_result.returncode != 0:
            # 检查是否是因为没有变更
            if "nothing to commit" in commit_result.stdout.lower():
                logger.info("没有变更需要提交")
                print("ℹ️ 没有变更需要提交", flush=True)
                return {
                    "status": "success",
                    "message": "没有变更需要提交",
                    "output": commit_result.stdout
                }
            else:
                error_msg = f"git commit 失败: {commit_result.stderr}"
                logger.error(error_msg)
                print(f"❌ {error_msg}", flush=True)
                return {
                    "status": "error",
                    "message": "git commit 失败",
                    "error": commit_result.stderr
                }
        
        logger.info("提交成功")
        print("✅ 提交成功", flush=True)
        print(f"📄 提交输出: {commit_result.stdout.strip()}", flush=True)
        
        return {
            "status": "success",
            "message": "提交成功",
            "output": commit_result.stdout.strip()
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "git commit 命令超时"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"git commit 时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

def git_push_changes(git_work_dir: str) -> Dict[str, Any]:
    """
    推送变更到远程仓库
    
    Args:
        git_work_dir: git 工作目录路径
        
    Returns:
        Dict[str, Any]: 推送结果
    """
    logger.info("推送变更到远程仓库")
    print("📤 推送变更到远程仓库", flush=True)
    
    try:
        # 执行 git push
        push_result = subprocess.run(
            ["git", "push"],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if push_result.returncode != 0:
            error_msg = f"git push 失败: {push_result.stderr}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": "git push 失败",
                "error": push_result.stderr
            }
        
        logger.info("推送成功")
        print("✅ 推送成功", flush=True)
        if push_result.stdout.strip():
            print(f"📄 推送输出: {push_result.stdout.strip()}", flush=True)
        
        return {
            "status": "success",
            "message": "推送成功",
            "output": push_result.stdout.strip()
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "git push 命令超时"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"git push 时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

def run_preparation_phase(config: AppConfig, note: str) -> Dict[str, Any]:
    """
    运行完整的准备阶段
    
    Args:
        config: 应用配置对象
        note: git 提交备注
        
    Returns:
        Dict[str, Any]: 准备阶段结果
    """
    logger.info("开始准备阶段")
    print("🚀 开始准备阶段", flush=True)
    
    # 1. 检查工作目录是否存在
    dir_check = check_git_work_dir_exists(config)
    if dir_check["status"] != "success":
        return dir_check
    
    git_work_dir = dir_check["path"]
    
    # 2. 检查当前 git 分支
    branch_check = check_current_git_branch(git_work_dir)
    if branch_check["status"] != "success":
        return branch_check
    
    # 3. git add . 并显示变更
    add_result = git_add_and_show_changes(git_work_dir)
    if add_result["status"] != "success":
        return add_result
    
    # 4. git commit
    commit_result = git_commit_with_note(git_work_dir, note)
    if commit_result["status"] != "success":
        return commit_result
    
    # 5. git push
    push_result = git_push_changes(git_work_dir)
    if push_result["status"] != "success":
        return push_result
    
    logger.info("准备阶段完成")
    print("🎉 准备阶段完成", flush=True)
    
    return {
        "status": "success",
        "message": "准备阶段完成",
        "git_work_dir": git_work_dir,
        "branch": branch_check.get("branch", "unknown"),
        "changes": add_result.get("changes", ""),
        "commit_output": commit_result.get("output", ""),
        "push_output": push_result.get("output", "")
    }
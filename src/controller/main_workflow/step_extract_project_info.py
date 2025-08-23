# controller/main_workflow/step_extract_project_info.py

import os
import subprocess
from clients.logging.logger import logger
from config.config_models import AppConfig
from typing import Dict, Any, Optional
import re

def extract_project_info_from_git(git_work_dir: str) -> Dict[str, Any]:
    """
    从 git 工作目录提取项目信息
    
    Args:
        git_work_dir: git 工作目录路径
        
    Returns:
        Dict[str, Any]: 项目信息
    """
    logger.info("从 git 工作目录提取项目信息")
    print("📋 提取项目信息", flush=True)
    
    try:
        # 获取远程 origin URL
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=git_work_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if remote_result.returncode != 0:
            error_msg = f"获取远程 URL 失败: {remote_result.stderr}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": "获取远程 URL 失败",
                "error": remote_result.stderr
            }
        
        remote_url = remote_result.stdout.strip()
        logger.info(f"远程 URL: {remote_url}")
        print(f"🔗 远程 URL: {remote_url}", flush=True)
        
        # 从 URL 提取项目名称
        project_name = extract_project_name_from_url(remote_url)
        if not project_name:
            error_msg = "无法从远程 URL 提取项目名称"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return {
                "status": "error",
                "message": error_msg,
                "remote_url": remote_url
            }
        
        logger.info(f"项目名称: {project_name}")
        print(f"📁 项目名称: {project_name}", flush=True)
        
        return {
            "status": "success",
            "message": "项目信息提取成功",
            "project_name": project_name,
            "remote_url": remote_url,
            "git_work_dir": git_work_dir
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
        error_msg = f"提取项目信息时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }

def extract_project_name_from_url(remote_url: str) -> Optional[str]:
    """
    从 git 远程 URL 提取项目名称
    支持多种 URL 格式：
    - SSH with port: ssh://git@gitlab.example.com:1022/group/project.git
    - SSH standard: git@gitlab.example.com:group/project.git
    - HTTPS: https://gitlab.example.com/group/project.git
    
    Args:
        remote_url: git 远程 URL
        
    Returns:
        Optional[str]: 项目名称，格式为 group/project
    """
    try:
        logger.debug(f"解析 URL: {remote_url}")
        
        # 使用正则表达式匹配不同格式的 URL
        patterns = [
            # SSH with port: ssh://git@gitlab.example.com:1022/group/project.git
            r'^ssh://[^@]+@[^:/]+:\d+/(.+?)(?:\.git)?/?$',
            # SSH standard: git@gitlab.example.com:group/project.git
            r'^[^@]+@[^:/]+:(.+?)(?:\.git)?/?$',
            # HTTPS: https://gitlab.example.com/group/project.git
            r'^https?://[^/]+/(.+?)(?:\.git)?/?$',
            # HTTP: http://gitlab.example.com/group/project.git
            r'^http://[^/]+/(.+?)(?:\.git)?/?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, remote_url)
            if match:
                path_part = match.group(1)
                logger.debug(f"匹配到路径: {path_part}")
                
                # 验证格式 (应该包含至少一个斜杠，表示 group/project)
                if "/" not in path_part:
                    logger.warning(f"项目路径格式不正确，缺少组织名: {path_part}")
                    continue
                
                # 确保路径不以斜杠开头或结尾
                path_part = path_part.strip("/")
                
                logger.info(f"成功提取项目名称: {path_part}")
                return path_part
        
        # 如果所有模式都不匹配，记录详细信息
        logger.error(f"所有 URL 模式都不匹配: {remote_url}")
        logger.error("支持的 URL 格式:")
        logger.error("- SSH with port: ssh://git@gitlab.example.com:1022/group/project.git")
        logger.error("- SSH standard: git@gitlab.example.com:group/project.git")
        logger.error("- HTTPS: https://gitlab.example.com/group/project.git")
        logger.error("- HTTP: http://gitlab.example.com/group/project.git")
        
        return None
        
    except Exception as e:
        logger.error(f"解析 URL 时出错: {e}")
        return None

def prepare_project_info_for_workflow(config: AppConfig, preparation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    为后续工作流准备项目信息
    
    Args:
        config: 应用配置对象
        preparation_result: 准备阶段的结果
        
    Returns:
        Dict[str, Any]: 为工作流准备的项目信息
    """
    logger.info("为工作流准备项目信息")
    
    git_work_dir = preparation_result["git_work_dir"]
    
    # 提取项目信息
    project_info = extract_project_info_from_git(git_work_dir)
    if project_info["status"] != "success":
        return project_info
    
    # 准备完整的项目信息
    workflow_project_info = {
        "status": "success",
        "message": "项目信息准备完成",
        "project_name": project_info["project_name"],
        "remote_url": project_info["remote_url"],
        "git_work_dir": git_work_dir,
        "branch": preparation_result.get("branch", "unknown"),
        "preparation_completed": True
    }
    
    logger.info(f"工作流项目信息准备完成: {workflow_project_info['project_name']}")
    print(f"✅ 项目信息准备完成: {workflow_project_info['project_name']}", flush=True)
    
    return workflow_project_info
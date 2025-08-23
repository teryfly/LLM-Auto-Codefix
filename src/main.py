# main.py

import sys
from clients.logging.logger import logger

BANNER = r"""
===============================================================
   LLM-Auto-Codefix CI/CD Pipeline Orchestrator (for GitLab)
===============================================================
"""

def get_user_note() -> str:
    """
    获取用户输入的 git commit 备注
    
    Returns:
        str: 用户输入的备注
    """
    try:
        note = input("请输入 git commit 备注: ").strip()
        if not note:
            note = "LLM Auto Codefix - Default commit"
            print(f"使用默认备注: {note}")
        return note
    except KeyboardInterrupt:
        print("\n[ABORT] 用户取消输入")
        sys.exit(130)
    except Exception as e:
        logger.warning(f"获取用户输入失败: {e}")
        default_note = "LLM Auto Codefix - Default commit"
        print(f"使用默认备注: {default_note}")
        return default_note

def run_preparation_phase(config, note: str) -> dict:
    """
    运行准备阶段
    
    Args:
        config: 应用配置
        note: git commit 备注
        
    Returns:
        dict: 准备阶段结果
    """
    from controller.main_workflow.step_preparation_phase import run_preparation_phase
    from controller.main_workflow.step_extract_project_info import prepare_project_info_for_workflow
    
    print("\n🚀 === 一、准备阶段 ===", flush=True)
    
    # 执行准备阶段
    preparation_result = run_preparation_phase(config, note)
    if preparation_result["status"] != "success":
        return preparation_result
    
    # 准备项目信息
    project_info = prepare_project_info_for_workflow(config, preparation_result)
    if project_info["status"] != "success":
        return project_info
    
    print("✅ 准备阶段完成\n", flush=True)
    return project_info

def run_debug_and_deployment_phase(config, project_info: dict) -> dict:
    """
    运行调试和部署阶段
    
    Args:
        config: 应用配置
        project_info: 项目信息
        
    Returns:
        dict: 执行结果
    """
    from controller.main_workflow.step_create_mr import create_merge_request
    from controller.main_workflow.step_debug_loop import run_debug_loop
    from controller.main_workflow.step_merge_mr import merge_mr_and_wait_pipeline
    from controller.main_workflow.step_post_merge_monitor import monitor_post_merge_pipeline
    
    print("🚀 === 二、调试阶段及后续 ===", flush=True)
    
    try:
        # 由于准备阶段已经完成了 git 操作，这里需要模拟原有的 project_info 格式
        # 从 project_info 中获取项目名称，并查询 GitLab 项目 ID
        from controller.input_project_controller import InputProjectController
        
        input_project_ctrl = InputProjectController()
        project_name = project_info["project_name"]
        
        logger.info(f"查询 GitLab 项目信息: {project_name}")
        print(f"🔍 查询 GitLab 项目信息: {project_name}", flush=True)
        
        _, encoded_path, project, project_id = input_project_ctrl.get_project_info(project_name)
        
        # 构建兼容的项目信息
        workflow_project_info = {
            "project_id": project_id,
            "project_name": project_name,
            "encoded_path": encoded_path,
            "local_dir": project_info["git_work_dir"],
        }
        
        print(f"✅ GitLab 项目信息获取成功: ID={project_id}", flush=True)
        
        # 创建 MR
        mr = create_merge_request(config, workflow_project_info)
        
        # 调试循环
        run_debug_loop(config, workflow_project_info, mr)
        
        # 合并 MR 并等待 Pipeline
        merge_mr_and_wait_pipeline(config, workflow_project_info, mr)
        
        # 监控合并后的 Pipeline
        monitor_post_merge_pipeline(config, workflow_project_info)
        
        return {
            "status": "success",
            "message": "调试和部署阶段完成"
        }
        
    except Exception as e:
        error_msg = f"调试和部署阶段失败: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        return {
            "status": "error",
            "message": error_msg
        }

def main():
    """
    主程序入口点
    新的执行流程：
    1. 准备阶段（检查目录、git 操作）
    2. 调试阶段及后续（MR 创建、调试循环、合并、监控）
    """
    try:
        # 显示横幅
        print(BANNER)
        
        # 获取用户输入的备注
        note = get_user_note()
        logger.info(f"用户输入的备注: {note}")
        
        # 延迟导入避免循环导入问题
        from controller.main_workflow.step_load_config import load_and_validate_config
        
        print("[INFO] Loading configuration from config.yaml ...")
        config = load_and_validate_config("config.yaml")
        
        # 一、准备阶段
        project_info = run_preparation_phase(config, note)
        if project_info["status"] != "success":
            print(f"❌ 准备阶段失败: {project_info['message']}", flush=True)
            sys.exit(1)
        
        # 二、调试阶段及后续
        result = run_debug_and_deployment_phase(config, project_info)
        if result["status"] != "success":
            print(f"❌ 调试和部署阶段失败: {result['message']}", flush=True)
            sys.exit(1)
        
        print("\n🎉 === 所有阶段完成 ===", flush=True)
        print("\n[FINISH] All tasks completed successfully.\n")
        print("Thank you for using LLM-Auto-Codefix!\n"
              "For logs and trace information, check the logs directory or designated output files.\n")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n[ABORT] User interrupted execution.")
        logger.warning("User interrupted execution")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n[FAIL] {e}\n")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
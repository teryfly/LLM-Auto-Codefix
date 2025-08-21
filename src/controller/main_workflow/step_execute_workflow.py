# controller/main_workflow/step_execute_workflow.py

from clients.logging.logger import logger
from typing import Dict, Any, Optional, TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from controller.main_controller import MainController

def execute_main_workflow(controller: "MainController", project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    执行主工作流程
    
    Args:
        controller: 主控制器实例
        project_name: 项目名称，可选参数
        
    Returns:
        Dict[str, Any]: 执行结果，包含状态和相关信息
        
    Raises:
        KeyboardInterrupt: 用户中断执行
        Exception: 工作流执行失败时抛出异常
    """
    logger.info("Starting main workflow execution")
    print("[INFO] Starting main workflow ...")
    
    try:
        # 执行主工作流
        controller.run(project_name)
        
        logger.info("Main workflow completed successfully")
        print("\n[FINISH] All tasks completed successfully.\n")
        
        return {
            "status": "success",
            "message": "All tasks completed successfully",
            "project_name": project_name
        }
        
    except KeyboardInterrupt:
        logger.warning("User interrupted execution")
        print("\n[ABORT] User interrupted execution.")
        sys.exit(130)
        
    except Exception as e:
        error_msg = f"Workflow execution failed: {e}"
        logger.error(error_msg)
        print(f"\n[FAIL] {e}\n")
        raise Exception(error_msg)

def run_workflow_with_error_handling(controller: "MainController", project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    带完整错误处理的工作流执行
    
    Args:
        controller: 主控制器实例
        project_name: 项目名称，可选参数
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    try:
        return execute_main_workflow(controller, project_name)
        
    except KeyboardInterrupt:
        return {
            "status": "interrupted",
            "message": "User interrupted execution",
            "exit_code": 130
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "error": str(e)
        }
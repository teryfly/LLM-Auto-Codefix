# controller/main_workflow/step_app_lifecycle.py

from typing import Dict, Any, Optional, TYPE_CHECKING
from clients.logging.logger import logger
from .step_display_banner import display_application_banner, display_completion_message
from .step_load_config import load_and_validate_config
from .step_init_controller import initialize_workflow_controller
from .step_execute_workflow import execute_main_workflow
from .step_error_handling import (
    handle_fatal_error,
    handle_keyboard_interrupt,
    handle_unhandled_error,
    safe_execute_step
)

if TYPE_CHECKING:
    from controller.main_controller import MainController

def initialize_application(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    初始化应用程序
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 初始化结果，包含配置和控制器
    """
    try:
        # 显示启动横幅
        display_application_banner()
        
        # 加载配置
        config_result = safe_execute_step(
            load_and_validate_config,
            "Load Configuration",
            config_path
        )
        
        if config_result["status"] != "success":
            return config_result
            
        config = config_result["result"]
        
        # 初始化控制器
        controller_result = safe_execute_step(
            initialize_workflow_controller,
            "Initialize Controller",
            config
        )
        
        if controller_result["status"] != "success":
            return controller_result
            
        controller = controller_result["result"]
        
        return {
            "status": "success",
            "message": "Application initialized successfully",
            "config": config,
            "controller": controller
        }
        
    except Exception as e:
        return handle_unhandled_error(e)

def run_application_workflow(
    controller: "MainController",
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    运行应用程序工作流
    
    Args:
        controller: 主控制器实例
        project_name: 项目名称，可选
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    try:
        # 执行主工作流
        workflow_result = safe_execute_step(
            execute_main_workflow,
            "Execute Main Workflow",
            controller,
            project_name
        )
        
        return workflow_result
        
    except KeyboardInterrupt:
        return handle_keyboard_interrupt()
    except Exception as e:
        return handle_unhandled_error(e)

def finalize_application(result: Dict[str, Any]) -> None:
    """
    完成应用程序执行
    
    Args:
        result: 应用程序执行结果
    """
    try:
        if result.get("status") == "success":
            display_completion_message()
        
        logger.info(f"Application finalized with status: {result.get('status', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error during application finalization: {e}")

def run_complete_application(
    config_path: str = "config.yaml",
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    运行完整的应用程序生命周期
    
    Args:
        config_path: 配置文件路径
        project_name: 项目名称，可选
        
    Returns:
        Dict[str, Any]: 最终执行结果
    """
    # 初始化应用程序
    init_result = initialize_application(config_path)
    
    if init_result["status"] != "success":
        finalize_application(init_result)
        return init_result
    
    # 运行工作流
    workflow_result = run_application_workflow(
        init_result["controller"],
        project_name
    )
    
    # 完成应用程序
    finalize_application(workflow_result)
    
    return workflow_result
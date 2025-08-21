# controller/main_workflow/step_init_controller.py

from config.config_models import AppConfig
from clients.logging.logger import logger
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from controller.main_controller import MainController

def initialize_workflow_controller(config: AppConfig) -> "MainController":
    """
    初始化工作流控制器
    
    Args:
        config: 应用配置对象
        
    Returns:
        MainController: 初始化完成的主控制器实例
        
    Raises:
        Exception: 控制器初始化失败时抛出异常
    """
    logger.info("Initializing workflow controller")
    print("[INFO] Initializing workflow controller ...")
    
    try:
        # 延迟导入避免循环导入
        from controller.main_controller import MainController
        
        controller = MainController(config)
        logger.info("Workflow controller initialized successfully")
        print("[SUCCESS] Workflow controller initialized.")
        return controller
        
    except Exception as e:
        error_msg = f"Controller initialization failed: {e}"
        logger.error(error_msg)
        print(f"[FATAL] {error_msg}")
        raise Exception(error_msg)

def create_controller_with_config(config_path: str = "config.yaml") -> "MainController":
    """
    便捷方法：加载配置并创建控制器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        MainController: 初始化完成的主控制器实例
    """
    from .step_load_config import load_and_validate_config
    
    config = load_and_validate_config(config_path)
    return initialize_workflow_controller(config)
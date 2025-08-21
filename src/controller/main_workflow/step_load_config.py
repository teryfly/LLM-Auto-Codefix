# controller/main_workflow/step_load_config.py

from config.config_manager import ConfigManager
from config.config_validator import validate_config
from config.config_models import AppConfig
from utils.helpers import exit_with_error
from clients.logging.logger import logger
from typing import Optional

def load_and_validate_config(config_path: str = "config.yaml") -> AppConfig:
    """
    加载并验证配置文件
    
    Args:
        config_path: 配置文件路径，默认为 "config.yaml"
        
    Returns:
        AppConfig: 验证通过的配置对象
        
    Raises:
        Exception: 配置加载或验证失败时抛出异常
    """
    logger.info(f"Loading configuration from {config_path}")
    print(f"[INFO] Loading configuration from {config_path} ...")
    
    try:
        config = ConfigManager.load_config(config_path)
        validate_config(config)
        logger.info("Configuration loaded and validated successfully")
        print("[SUCCESS] Configuration loaded and validated.")
        return config
        
    except Exception as e:
        error_msg = f"Configuration error: {e}"
        logger.error(error_msg)
        print(f"[FATAL] {error_msg}")
        raise Exception(error_msg)

def get_config() -> Optional[AppConfig]:
    """
    获取已加载的配置对象
    
    Returns:
        AppConfig: 配置对象，如果未加载则返回 None
    """
    try:
        return ConfigManager.get_config()
    except RuntimeError:
        return None
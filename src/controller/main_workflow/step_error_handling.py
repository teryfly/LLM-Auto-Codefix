# controller/main_workflow/step_error_handling.py

from utils.helpers import exit_with_error
from clients.logging.logger import logger
from typing import Dict, Any, Optional, Callable
import sys
import traceback

def handle_fatal_error(error: Exception, context: str = "Application") -> None:
    """
    处理致命错误并退出程序
    
    Args:
        error: 异常对象
        context: 错误上下文描述
    """
    error_msg = f"{context} error: {error}"
    logger.error(f"Fatal error occurred: {error_msg}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    exit_with_error(f"[FATAL] {error_msg}")

def handle_workflow_error(error: Exception, step_name: str = "Unknown") -> Dict[str, Any]:
    """
    处理工作流错误并返回错误信息
    
    Args:
        error: 异常对象
        step_name: 出错的步骤名称
        
    Returns:
        Dict[str, Any]: 错误信息字典
    """
    error_msg = f"Step '{step_name}' failed: {error}"
    logger.error(error_msg)
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {
        "status": "error",
        "step": step_name,
        "message": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc()
    }

def safe_execute_step(
    step_func: Callable,
    step_name: str,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    安全执行步骤函数，捕获并处理异常
    
    Args:
        step_func: 要执行的步骤函数
        step_name: 步骤名称
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    try:
        logger.info(f"Executing step: {step_name}")
        result = step_func(*args, **kwargs)
        
        if isinstance(result, dict):
            result["step"] = step_name
            result["status"] = result.get("status", "success")
        else:
            result = {
                "step": step_name,
                "status": "success",
                "result": result
            }
            
        logger.info(f"Step '{step_name}' completed successfully")
        return result
        
    except Exception as e:
        return handle_workflow_error(e, step_name)

def handle_keyboard_interrupt() -> Dict[str, Any]:
    """
    处理键盘中断
    
    Returns:
        Dict[str, Any]: 中断信息
    """
    logger.warning("User interrupted execution")
    print("\n[ABORT] User interrupted execution.")
    
    return {
        "status": "interrupted",
        "message": "User interrupted execution",
        "exit_code": 130
    }

def handle_unhandled_error(error: Exception) -> Dict[str, Any]:
    """
    处理未捕获的错误
    
    Args:
        error: 异常对象
        
    Returns:
        Dict[str, Any]: 错误信息
    """
    error_msg = f"Unhandled error: {error}"
    logger.error(error_msg)
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"\n[FAIL] {error}\n")
    
    return {
        "status": "fatal_error",
        "message": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc()
    }
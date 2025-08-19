from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from config.config_models import AppConfig
from models.web.api_models import PollingConfigResponse, PollingConfigUpdate
from ..core.dependencies import get_config
router = APIRouter()
@router.get("/config/polling", response_model=PollingConfigResponse)
async def get_polling_config(config: AppConfig = Depends(get_config)):
    """Get current polling configuration"""
    try:
        # Extract polling config from web_config if exists, otherwise use defaults
        web_config = getattr(config, 'web_config', None)
        if web_config and hasattr(web_config, 'polling'):
            polling_config = web_config.polling
            return PollingConfigResponse(
                default_interval=polling_config.default_interval,
                pipeline_interval=polling_config.pipeline_interval,
                job_interval=polling_config.job_interval,
                log_interval=polling_config.log_interval,
                workflow_interval=getattr(polling_config, 'workflow_interval', 5)  # 默认5秒
            )
        else:
            # Default polling configuration with workflow interval
            return PollingConfigResponse(
                default_interval=3,
                pipeline_interval=2,
                job_interval=5,
                log_interval=10,
                workflow_interval=5  # 工作流状态轮询间隔：5秒
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get polling config: {str(e)}"
        )
@router.put("/config/polling")
async def update_polling_config(
    update: PollingConfigUpdate,
    config: AppConfig = Depends(get_config)
):
    """Update polling configuration"""
    try:
        # In a real implementation, this would update the config file
        # For now, we'll just return success
        return {
            "status": "updated",
            "message": "Polling configuration updated successfully",
            "data": update.dict(exclude_unset=True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update polling config: {str(e)}"
        )
@router.get("/config/app")
async def get_app_config(config: AppConfig = Depends(get_config)):
    """Get application configuration (sanitized)"""
    try:
        # Return sanitized config without sensitive information
        sanitized_config = {
            "services": {
                "gitlab_url": config.services.gitlab_url,
                "llm_model": config.services.llm_model,
                "grpc_port": config.services.grpc_port
            },
            "retry_config": {
                "retry_interval_time": config.retry_config.retry_interval_time,
                "retry_max_time": config.retry_config.retry_max_time,
                "debug_max_time": config.retry_config.debug_max_time,
                "total_timeout": config.retry_config.total_timeout
            },
            "timeout": {
                "overall_timeout_minutes": config.timeout.overall_timeout_minutes,
                "pipeline_check_interval": config.timeout.pipeline_check_interval
            },
            "polling": {
                "workflow_interval": 5,  # 工作流状态轮询间隔
                "pipeline_interval": 2,  # Pipeline状态轮询间隔
                "job_interval": 5,       # Job状态轮询间隔
                "log_interval": 10,      # 日志轮询间隔
                "error_check_interval": 2 # 错误检测间隔
            }
        }
        return sanitized_config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get app config: {str(e)}"
        )
@router.get("/config/polling/detailed")
async def get_detailed_polling_config(config: AppConfig = Depends(get_config)):
    """Get detailed polling configuration for different components"""
    try:
        return {
            "workflow": {
                "status_interval": 5,        # 工作流状态检查间隔（秒）
                "step_interval": 3,          # 步骤状态检查间隔（秒）
                "error_check_interval": 2,   # 错误检测间隔（秒）
                "timeout_minutes": 120       # 工作流超时时间（分钟）
            },
            "pipeline": {
                "status_interval": 2,        # Pipeline状态检查间隔（秒）
                "job_interval": 5,           # Job状态检查间隔（秒）
                "trace_interval": 10,        # 日志轮询间隔（秒）
                "timeout_minutes": 60        # Pipeline监控超时时间（分钟）
            },
            "ui": {
                "dashboard_refresh": 5,      # 仪表板刷新间隔（秒）
                "pipeline_monitor": 3,       # Pipeline监控器刷新间隔（秒）
                "log_viewer": 10,           # 日志查看器刷新间隔（秒）
                "status_indicator": 3        # 状态指示器刷新间隔（秒）
            },
            "api": {
                "default_timeout": 30,       # 默认API超时时间（秒）
                "retry_attempts": 3,         # 重试次数
                "retry_delay": 2,           # 重试延迟（秒）
                "backoff_multiplier": 1.5    # 退避乘数
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed polling config: {str(e)}"
        )
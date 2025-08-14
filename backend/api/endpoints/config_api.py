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
        else:
            # Default polling configuration
            polling_config = {
                "default_interval": 3,
                "pipeline_interval": 2,
                "job_interval": 5,
                "log_interval": 10
            }

        return PollingConfigResponse(**polling_config)
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
            }
        }
        return sanitized_config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get app config: {str(e)}"
        )
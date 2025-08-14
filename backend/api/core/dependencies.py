from fastapi import Depends, HTTPException, status
from typing import Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_manager import ConfigManager
from config.config_models import AppConfig
from services.web.session_service import SessionService
from services.web.workflow_service import WorkflowService
from services.web.gitlab_proxy_service import GitLabProxyService
from services.web.pipeline_monitor_service import PipelineMonitorService

# Global instances
_config: Optional[AppConfig] = None
_session_service: Optional[SessionService] = None
_workflow_service: Optional[WorkflowService] = None
_gitlab_proxy_service: Optional[GitLabProxyService] = None
_pipeline_monitor_service: Optional[PipelineMonitorService] = None

def get_config() -> AppConfig:
    global _config
    if _config is None:
        try:
            config_path = project_root / "config.yaml"
            _config = ConfigManager.load_config(str(config_path))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load configuration: {str(e)}"
            )
    return _config

def get_session_service(config: AppConfig = Depends(get_config)) -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService(config)
    return _session_service

def get_workflow_service(
    config: AppConfig = Depends(get_config),
    session_service: SessionService = Depends(get_session_service)
) -> WorkflowService:
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService(config, session_service)
    return _workflow_service

def get_gitlab_proxy_service(config: AppConfig = Depends(get_config)) -> GitLabProxyService:
    global _gitlab_proxy_service
    if _gitlab_proxy_service is None:
        _gitlab_proxy_service = GitLabProxyService(config)
    return _gitlab_proxy_service

def get_pipeline_monitor_service(
    config: AppConfig = Depends(get_config),
    gitlab_service: GitLabProxyService = Depends(get_gitlab_proxy_service)
) -> PipelineMonitorService:
    global _pipeline_monitor_service
    if _pipeline_monitor_service is None:
        _pipeline_monitor_service = PipelineMonitorService(config, gitlab_service)
    return _pipeline_monitor_service
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
class WorkflowPollingConfig(BaseModel):
    """Configuration for workflow status polling"""
    status_interval: int = Field(default=5, ge=1, le=30, description="Workflow status check interval in seconds")
    step_interval: int = Field(default=3, ge=1, le=20, description="Individual step status check interval in seconds")
    error_check_interval: int = Field(default=2, ge=1, le=10, description="Error detection check interval in seconds")
    timeout_minutes: int = Field(default=120, ge=5, le=480, description="Maximum workflow timeout in minutes")
    @validator('status_interval', 'step_interval', 'error_check_interval')
    def validate_intervals(cls, v):
        if v < 1:
            raise ValueError("Interval must be at least 1 second")
        return v
class PipelinePollingConfig(BaseModel):
    """Configuration for pipeline monitoring polling"""
    status_interval: int = Field(default=2, ge=1, le=30, description="Pipeline status check interval in seconds")
    job_interval: int = Field(default=5, ge=1, le=60, description="Job status check interval in seconds")
    trace_interval: int = Field(default=10, ge=5, le=120, description="Job trace polling interval in seconds")
    timeout_minutes: int = Field(default=60, ge=5, le=480, description="Maximum monitoring timeout in minutes")
    @validator('status_interval', 'job_interval', 'trace_interval')
    def validate_intervals(cls, v):
        if v < 1:
            raise ValueError("Interval must be at least 1 second")
        return v
class UIPollingConfig(BaseModel):
    """Configuration for UI component polling"""
    dashboard_refresh: int = Field(default=5, ge=2, le=60, description="Dashboard refresh interval in seconds")
    pipeline_monitor: int = Field(default=3, ge=1, le=30, description="Pipeline monitor refresh interval in seconds")
    log_viewer: int = Field(default=10, ge=5, le=120, description="Log viewer refresh interval in seconds")
    status_indicator: int = Field(default=3, ge=1, le=15, description="Status indicator refresh interval in seconds")
class APIPollingConfig(BaseModel):
    """Configuration for API polling behavior"""
    default_timeout: int = Field(default=30, ge=5, le=300, description="Default API timeout in seconds")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts for failed requests")
    retry_delay: int = Field(default=2, ge=1, le=30, description="Delay between retry attempts in seconds")
    backoff_multiplier: float = Field(default=1.5, ge=1.0, le=5.0, description="Backoff multiplier for retries")
class PollingConfiguration(BaseModel):
    """Complete polling configuration"""
    enabled: bool = Field(default=True, description="Enable/disable polling globally")
    workflow: WorkflowPollingConfig = Field(default_factory=WorkflowPollingConfig)
    pipeline: PipelinePollingConfig = Field(default_factory=PipelinePollingConfig)
    ui: UIPollingConfig = Field(default_factory=UIPollingConfig)
    api: APIPollingConfig = Field(default_factory=APIPollingConfig)
    def get_interval(self, poll_type: str, component: str) -> int:
        """Get polling interval for specific type and component"""
        config_map = {
            "pipeline": self.pipeline,
            "workflow": self.workflow,
            "ui": self.ui
        }
        if poll_type not in config_map:
            return self.workflow.status_interval  # Default fallback
        config_obj = config_map[poll_type]
        return getattr(config_obj, f"{component}_interval", self.workflow.status_interval)
    def get_timeout(self, operation_type: str = "default") -> int:
        """Get timeout for specific operation type"""
        if operation_type == "pipeline":
            return self.pipeline.timeout_minutes * 60
        elif operation_type == "workflow":
            return self.workflow.timeout_minutes * 60
        return self.api.default_timeout
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PollingConfiguration":
        """Create configuration from dictionary"""
        return cls(**data)
    def to_frontend_config(self) -> Dict[str, Any]:
        """Convert to frontend-compatible configuration"""
        return {
            "enabled": self.enabled,
            "intervals": {
                "dashboard": self.ui.dashboard_refresh,
                "pipeline": self.ui.pipeline_monitor,
                "logs": self.ui.log_viewer,
                "status": self.ui.status_indicator,
                "workflow": self.workflow.status_interval,
                "workflow_step": self.workflow.step_interval,
                "error_check": self.workflow.error_check_interval
            },
            "timeouts": {
                "api": self.api.default_timeout,
                "pipeline": self.pipeline.timeout_minutes * 60,
                "workflow": self.workflow.timeout_minutes * 60
            },
            "retry": {
                "attempts": self.api.retry_attempts,
                "delay": self.api.retry_delay,
                "backoff": self.api.backoff_multiplier
            }
        }
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class PipelinePollingConfig(BaseModel):
    """Configuration for pipeline monitoring polling"""

    status_interval: int = Field(default=2, ge=1, le=30, description="Pipeline status check interval in seconds")
    job_interval: int = Field(default=5, ge=1, le=60, description="Job status check interval in seconds")
    trace_interval: int = Field(default=10, ge=5, le=120, description="Job trace polling interval in seconds")
    timeout_minutes: int = Field(default=60, ge=5, le=480, description="Maximum monitoring timeout in minutes")

    @validator('status_interval', 'job_interval', 'trace_interval')
    def validate_intervals(cls, v):
        if v  int:
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
                "workflow": self.workflow.status_interval
            },
            "timeouts": {
                "api": self.api.default_timeout,
                "pipeline": self.pipeline.timeout_minutes * 60
            },
            "retry": {
                "attempts": self.api.retry_attempts,
                "delay": self.api.retry_delay,
                "backoff": self.api.backoff_multiplier
            }
        }
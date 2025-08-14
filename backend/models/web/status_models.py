from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceStatus(BaseModel):
    name: str
    status: ComponentStatus
    message: Optional[str] = None
    last_check: datetime
    response_time: Optional[float] = None

    class Config:
        use_enum_values = True

class SystemStatus(BaseModel):
    overall_status: ComponentStatus
    services: List[ServiceStatus]
    active_sessions: int
    running_workflows: int
    system_info: Dict[str, Any]
    timestamp: datetime

    class Config:
        use_enum_values = True

class StatusUpdate(BaseModel):
    session_id: str
    workflow_status: str
    current_step: str
    step_progress: Dict[str, Any]
    pipeline_status: Optional[str] = None
    job_statuses: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    timestamp: datetime

class ProgressInfo(BaseModel):
    current_step: int
    total_steps: int
    step_name: str
    step_display_name: str
    progress_percent: float
    estimated_remaining: Optional[int] = None
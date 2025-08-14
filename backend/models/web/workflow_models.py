from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStep(BaseModel):
    name: str
    display_name: str
    status: StepStatus
    description: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

class WorkflowState(BaseModel):
    session_id: str
    status: str
    current_step: str
    steps: Dict[str, WorkflowStep]
    project_info: Optional[Dict[str, Any]] = None
    pipeline_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)

    def add_log(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        self.updated_at = datetime.utcnow()

class WorkflowResult(BaseModel):
    session_id: str
    status: str
    project_info: Optional[Dict[str, Any]] = None
    pipeline_info: Optional[Dict[str, Any]] = None
    deployment_url: Optional[str] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
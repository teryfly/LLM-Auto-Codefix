from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.workflow_models import WorkflowStep

class WorkflowStartRequest(BaseModel):
    project_name: Optional[str] = Field(default="ai/dotnet-ai-demo", description="GitLab project name")
    source_branch: Optional[str] = Field(default="ai", description="Source branch name")
    target_branch: Optional[str] = Field(default="dev", description="Target branch name")
    auto_merge: Optional[bool] = Field(default=True, description="Auto merge on success")
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Configuration overrides")

class WorkflowStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

class WorkflowStopRequest(BaseModel):
    force: bool = Field(default=False, description="Force stop the workflow")

class WorkflowStatusResponse(BaseModel):
    session_id: str
    status: str
    current_step: str
    steps: Dict[str, WorkflowStep]
    project_info: Optional[Dict[str, Any]] = None
    pipeline_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PipelineStatusResponse(BaseModel):
    session_id: str
    pipeline_id: Optional[int] = None
    project_id: Optional[int] = None
    status: str
    ref: Optional[str] = None
    sha: Optional[str] = None
    web_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class JobStatusResponse(BaseModel):
    id: int
    name: str
    status: str
    stage: Optional[str] = None
    ref: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    web_url: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None

class TaskListResponse(BaseModel):
    tasks: List[TaskStatusResponse]

class PollingConfigResponse(BaseModel):
    default_interval: int = Field(default=3, description="Default polling interval in seconds")
    pipeline_interval: int = Field(default=2, description="Pipeline status polling interval")
    job_interval: int = Field(default=5, description="Job status polling interval")
    log_interval: int = Field(default=10, description="Log polling interval")
    workflow_interval: int = Field(default=5, description="Workflow status polling interval")

class PollingConfigUpdate(BaseModel):
    default_interval: Optional[int] = None
    pipeline_interval: Optional[int] = None
    job_interval: Optional[int] = None
    log_interval: Optional[int] = None
    workflow_interval: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
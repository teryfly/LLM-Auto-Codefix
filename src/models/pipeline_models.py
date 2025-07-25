from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class PipelineStatus(BaseModel):
    status: str
    details: Optional[str] = None
    updated_at: Optional[str] = None

class JobStatus(BaseModel):
    id: int
    name: str
    status: str
    stage: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    trace: Optional[str] = None

class StatusTransition(BaseModel):
    from_status: str
    to_status: str
    reason: Optional[str] = None

class PipelineMonitorResult(BaseModel):
    pipeline_id: int
    current_status: str
    job_statuses: List[JobStatus]
    last_checked: Optional[str]
    completed: bool = False
    failed: bool = False

class ManualStatusWait(BaseModel):
    job_id: int
    job_name: str
    pipeline_id: int
    wait_reason: Optional[str] = None
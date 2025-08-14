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

from models.web.workflow_models import WorkflowState

class SessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Session(BaseModel):
    id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    workflow_state: Optional[WorkflowState] = None
    logs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

class SessionInfo(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    workflow_status: Optional[str] = None
    current_step: Optional[str] = None

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    total: int
    active_count: int
    expired_count: int
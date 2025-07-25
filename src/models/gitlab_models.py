# models/gitlab_models.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class GitLabProject(BaseModel):
    id: int
    name: str
    path_with_namespace: str
    visibility: str
    web_url: Optional[str] = None

class GitLabPipeline(BaseModel):
    id: int
    status: str
    ref: str
    sha: str
    web_url: Optional[str] = None

class GitLabJob(BaseModel):
    id: int
    status: str
    stage: Optional[str] = None
    name: str
    ref: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

class MergeRequest(BaseModel):
    id: int
    iid: int
    project_id: int
    source_branch: str
    target_branch: str
    state: str
    title: str
    web_url: Optional[str] = None

class GitLabAPIError(BaseModel):
    message: str
    status_code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
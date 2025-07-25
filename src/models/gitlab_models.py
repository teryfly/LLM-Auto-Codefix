from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GitLabProject(BaseModel):
    id: int
    name: str
    path_with_namespace: str
    visibility: str
    web_url: Optional[str]

class GitLabPipeline(BaseModel):
    id: int
    status: str
    ref: str
    sha: str
    web_url: Optional[str]

class GitLabJob(BaseModel):
    id: int
    status: str
    stage: str
    name: str
    ref: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    trace: Optional[str]

class MergeRequest(BaseModel):
    id: int
    iid: int
    project_id: int
    source_branch: str
    target_branch: str
    state: str
    title: str
    web_url: Optional[str]

class GitLabAPIError(BaseModel):
    message: str
    status_code: Optional[int]
    details: Optional[Dict[str, Any]]
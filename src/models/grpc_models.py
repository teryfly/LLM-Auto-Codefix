from pydantic import BaseModel
from typing import Optional, Dict, Any

class GRPCRequest(BaseModel):
    project_id: str
    operation: str
    data: Optional[Dict[str, Any]]

class GRPCResponse(BaseModel):
    status: str
    message: Optional[str]
    payload: Optional[Dict[str, Any]]

class SourceConcatRequest(BaseModel):
    project_path: str

class SourceConcatResponse(BaseModel):
    document: str
    status: str
    message: Optional[str]
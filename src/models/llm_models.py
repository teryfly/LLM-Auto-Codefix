from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LLMMessage(BaseModel):
    role: str
    content: str

class LLMRequest(BaseModel):
    model: str
    messages: List[LLMMessage]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 2048

class LLMResponseChoice(BaseModel):
    index: int
    message: LLMMessage
    finish_reason: Optional[str]

class LLMResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[LLMResponseChoice]
    usage: Optional[Dict[str, Any]]

class LLMErrorResponse(BaseModel):
    error: Dict[str, Any]
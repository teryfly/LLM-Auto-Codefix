# config/config_models.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class PathsConfig(BaseModel):
    git_work_dir: str
    ai_work_dir: str

class ServicesConfig(BaseModel):
    grpc_port: str
    gitlab_url: str
    llm_url: str
    llm_model: str

class AuthConfig(BaseModel):
    gitlab_private_token: str

class RetryConfig(BaseModel):
    retry_interval_time: int
    retry_max_time: int
    debug_max_time: int
    total_timeout: int

class TimeoutConfig(BaseModel):
    overall_timeout_minutes: int
    pipeline_check_interval: int

class TemplatesConfig(BaseModel):
    fix_bug_prompt: str

class AppConfig(BaseModel):
    paths: PathsConfig
    services: ServicesConfig
    authentication: AuthConfig
    retry_config: RetryConfig
    timeout: TimeoutConfig
    templates: TemplatesConfig

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        return cls(
            paths=PathsConfig(**data["paths"]),
            services=ServicesConfig(**data["services"]),
            authentication=AuthConfig(**data["authentication"]),
            retry_config=RetryConfig(**data["retry_config"]),
            timeout=TimeoutConfig(**data["timeout"]),
            templates=TemplatesConfig(**data["templates"]),
        )
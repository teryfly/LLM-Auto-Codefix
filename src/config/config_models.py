# config/config_models.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class PathsConfig(BaseModel):
    git_work_dir: str
    ai_work_dir: str

class ServicesConfig(BaseModel):
    grpc_port: str
    gitlab_url: str
    gitlab_http_url: str
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
    system_prompt: str = Field(
        default="你一个是CICD助手，用户在提交代码后，运行CICD的过程中接收到pipline的日志如下，请分析问题给出解决方案。",
        description="LLM系统提示词"
    )

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
            templates=TemplatesConfig(**data.get("templates", {})),
        )
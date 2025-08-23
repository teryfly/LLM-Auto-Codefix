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
    debug_loop_interval: int = Field(
        default=10,
        description="调试循环间隔时间（秒）"
    )
class TimeoutConfig(BaseModel):
    overall_timeout_minutes: int
    pipeline_check_interval: int
class AppConfig(BaseModel):
    paths: PathsConfig
    services: ServicesConfig
    authentication: AuthConfig
    retry_config: RetryConfig
    timeout: TimeoutConfig
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        return cls(
            paths=PathsConfig(**data["paths"]),
            services=ServicesConfig(**data["services"]),
            authentication=AuthConfig(**data["authentication"]),
            retry_config=RetryConfig(**data.get("retry_config", {})),
            timeout=TimeoutConfig(**data["timeout"]),
        )
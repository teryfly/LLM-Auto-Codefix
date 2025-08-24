# config/config_models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

class PathsConfig(BaseModel):
    git_work_dir: str
    ai_work_dir: str

class ServicesConfig(BaseModel):
    grpc_port: str
    gitlab_url: str
    gitlab_http_url: str
    llm_url: str
    llm_model: str
    
    def get_llm_models(self) -> List[str]:
        """
        解析LLM模型配置，支持单个模型或用|分隔的多个模型
        
        Returns:
            List[str]: 模型列表
        """
        if "|" in self.llm_model:
            models = [model.strip() for model in self.llm_model.split("|") if model.strip()]
            logging.getLogger(__name__).info(f"解析到多个LLM模型: {models}")
            return models
        else:
            models = [self.llm_model.strip()]
            logging.getLogger(__name__).info(f"解析到单个LLM模型: {models}")
            return models

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
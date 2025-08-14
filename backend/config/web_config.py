from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig

class PollingConfig(BaseModel):
    default_interval: int = Field(default=3, description="Default polling interval in seconds")
    pipeline_interval: int = Field(default=2, description="Pipeline status polling interval")
    job_interval: int = Field(default=5, description="Job status polling interval")
    log_interval: int = Field(default=10, description="Log polling interval")
    max_retries: int = Field(default=3, description="Maximum retry attempts for failed polls")

class SessionConfig(BaseModel):
    timeout_minutes: int = Field(default=120, description="Session timeout in minutes")
    max_concurrent: int = Field(default=10, description="Maximum concurrent sessions")
    cleanup_interval: int = Field(default=300, description="Session cleanup interval in seconds")

class WebServerConfig(BaseModel):
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    log_level: str = Field(default="info", description="Logging level")

class CORSConfig(BaseModel):
    allow_origins: list = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"], description="Allowed CORS origins")
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    allow_methods: list = Field(default=["*"], description="Allowed HTTP methods")
    allow_headers: list = Field(default=["*"], description="Allowed HTTP headers")

class WebConfig(BaseModel):
    polling: PollingConfig = Field(default_factory=PollingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    server: WebServerConfig = Field(default_factory=WebServerConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)

class ExtendedAppConfig(AppConfig):
    """Extended app config with web-specific settings"""
    web_config: WebConfig = Field(default_factory=WebConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtendedAppConfig":
        # Get base config
        base_config = super().from_dict(data)

        # Add web config if present
        web_data = data.get("web_config", {})
        web_config = WebConfig(**web_data)

        # Create extended config
        extended_data = base_config.dict()
        extended_data["web_config"] = web_config

        return cls(**extended_data)

def load_web_config(config_path: str) -> ExtendedAppConfig:
    """Load configuration with web extensions"""
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    return ExtendedAppConfig.from_dict(raw_data)
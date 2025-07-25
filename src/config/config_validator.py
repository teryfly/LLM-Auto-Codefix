from .config_manager import ConfigManager
from .config_models import AppConfig
from pydantic import ValidationError

def validate_config(config: AppConfig) -> None:
    try:
        config.paths
        config.services
        config.authentication
        config.retry_config
        config.templates
    except AttributeError as e:
        raise ValueError(f"Missing required config section: {e}")
    if not hasattr(config.services, "gitlab_http_url"):
        raise ValueError("services.gitlab_http_url is required for GitLab API access")
    # Example value range checks
    if config.retry_config.retry_interval_time <= 0:
        raise ValueError("retry_interval_time must be > 0")
    if config.retry_config.retry_max_time < 1:
        raise ValueError("retry_max_time must be >= 1")
    if config.retry_config.debug_max_time < 1:
        raise ValueError("debug_max_time must be >= 1")
    if config.retry_config.total_timeout < 60:
        raise ValueError("total_timeout must be >= 60")
        

    # Add further schema or value checks as needed

def safe_load_and_validate(path: str) -> AppConfig:
    config = ConfigManager.load_config(path)
    validate_config(config)
    return config
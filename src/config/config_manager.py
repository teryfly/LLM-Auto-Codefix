# config/config_manager.py

import yaml
from typing import Any, Dict
from .config_models import AppConfig

class ConfigManager:
    _config: AppConfig = None

    @classmethod
    def load_config(cls, path: str) -> AppConfig:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        cls._config = AppConfig.from_dict(raw)
        return cls._config

    @classmethod
    def get_config(cls) -> AppConfig:
        if cls._config is None:
            raise RuntimeError("Configuration not loaded.")
        return cls._config

    @classmethod
    def reload(cls, path: str) -> AppConfig:
        cls._config = None
        return cls.load_config(path)
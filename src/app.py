from config.config_manager import ConfigManager
from config.config_models import AppConfig

class App:
    def __init__(self, config_path: str = "config.yaml"):
        self.config: AppConfig = ConfigManager.load_config(config_path)

    def get_config(self) -> AppConfig:
        return self.config

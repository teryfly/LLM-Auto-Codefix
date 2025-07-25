from config.config_manager import ConfigManager

class TemplateManager:
    def __init__(self):
        self.templates = ConfigManager.get_config().templates

    def get_fix_bug_prompt(self) -> str:
        return self.templates.fix_bug_prompt
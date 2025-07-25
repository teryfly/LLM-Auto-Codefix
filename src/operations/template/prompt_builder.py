# operations/template/prompt_builder.py

from .template_manager import TemplateManager

class PromptBuilder:
    def __init__(self):
        self.template_manager = TemplateManager()

    def build_fix_bug_prompt(self, trace: str, source_code: str) -> str:
        template = self.template_manager.get_fix_bug_prompt()
        return template.format(trace=trace, source_code=source_code)
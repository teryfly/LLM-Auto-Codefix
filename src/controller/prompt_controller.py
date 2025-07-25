# controller/prompt_controller.py

from operations.template.prompt_builder import PromptBuilder
from clients.logging.logger import logger

class PromptController:
    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def build_fix_prompt(self, trace, source_code):
        prompt = self.prompt_builder.build_fix_bug_prompt(trace, source_code)
        logger.info("提示词生成完成")
        return prompt
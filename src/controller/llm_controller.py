# controller/llm_controller.py

from clients.llm.llm_client import LLMClient
from clients.logging.logger import logger
import time

class LLMController:
    def __init__(self, config):
        self.llm_client = LLMClient()
        self.retry_time = config.retry_config.retry_max_time
        self.retry_interval = config.retry_config.retry_interval_time

    def fix_code_with_llm(self, prompt):
        for attempt in range(self.retry_time):
            try:
                result = self.llm_client.fix_code(prompt)
                logger.info(f"LLM响应成功，响应长度: {len(result)}")
                return result
            except Exception as e:
                logger.warning(f"LLM请求失败: {e}, retry {attempt+1}/{self.retry_time}")
                time.sleep(self.retry_interval)
        logger.error("LLM修复请求多次失败，终止。")
        return ""
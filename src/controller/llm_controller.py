# controller/llm_controller.py

from clients.llm.llm_client import LLMClient
from clients.logging.logger import logger
import time
import sys

class LLMController:
    def __init__(self, config):
        self.llm_client = LLMClient()
        self.retry_time = config.retry_config.retry_max_time
        self.retry_interval = config.retry_config.retry_interval_time

    def fix_code_with_llm(self, prompt):
        """非流式修复代码（保持向后兼容）"""
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

    def fix_code_with_llm_stream(self, prompt):
        """流式修复代码"""
        try:
            logger.info("开始流式LLM修复...")
            print(f"🤖 AI分析开始...", flush=True)
            
            full_response = ""
            for chunk in self.llm_client.fix_code_stream(prompt):
                full_response += chunk
                # 实时输出到控制台，确保workflow executor能捕获
                print(chunk, end="", flush=True)
                sys.stdout.flush()
            
            print(f"\n🤖 AI分析完成，响应长度: {len(full_response)}", flush=True)
            logger.info(f"流式LLM响应成功，响应长度: {len(full_response)}")
            return full_response
            
        except Exception as e:
            error_msg = f"流式LLM请求失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return ""

    def analyze_pipeline_logs(self, logs):
        """分析Pipeline日志"""
        try:
            logger.info("开始分析Pipeline日志...")
            print(f"🔍 开始分析Pipeline日志...", flush=True)
            
            full_response = ""
            for chunk in self.llm_client.analyze_pipeline_logs(logs):
                full_response += chunk
                # 实时输出到控制台
                print(chunk, end="", flush=True)
                sys.stdout.flush()
            
            print(f"\n✅ 日志分析完成", flush=True)
            logger.info(f"Pipeline日志分析完成，响应长度: {len(full_response)}")
            return full_response
            
        except Exception as e:
            error_msg = f"Pipeline日志分析失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return ""
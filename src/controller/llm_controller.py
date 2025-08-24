# controller/llm_controller.py

from clients.llm.llm_client import LLMClient
from clients.logging.logger import logger
import time
import sys
from typing import Optional, List

class LLMController:
    def __init__(self, config):
        self.llm_client = LLMClient()
        self.retry_time = config.retry_config.retry_max_time
        self.retry_interval = config.retry_config.retry_interval_time
        self.available_models = self.llm_client.get_available_models()
        self.current_model_index = 0
        
        logger.info(f"LLM控制器初始化完成，可用模型: {self.available_models}")
        print(f"🤖 可用LLM模型: {', '.join(self.available_models)}", flush=True)

    def get_current_model(self) -> Optional[str]:
        """
        获取当前使用的模型
        
        Returns:
            Optional[str]: 当前模型名称，如果没有可用模型则返回None
        """
        if self.current_model_index < len(self.available_models):
            return self.available_models[self.current_model_index]
        return None

    def switch_to_next_model(self) -> bool:
        """
        切换到下一个模型
        
        Returns:
            bool: 是否成功切换到下一个模型
        """
        self.current_model_index += 1
        if self.current_model_index < len(self.available_models):
            current_model = self.available_models[self.current_model_index]
            logger.info(f"切换到下一个模型: {current_model} (索引: {self.current_model_index})")
            print(f"🔄 切换到下一个模型: {current_model}", flush=True)
            return True
        else:
            logger.error("已经尝试了所有可用模型")
            print("❌ 已经尝试了所有可用模型", flush=True)
            return False

    def reset_model_index(self):
        """
        重置模型索引到第一个模型
        """
        self.current_model_index = 0
        if self.available_models:
            logger.info(f"重置到第一个模型: {self.available_models[0]}")
            print(f"🔄 重置到第一个模型: {self.available_models[0]}", flush=True)

    def has_more_models(self) -> bool:
        """
        检查是否还有更多模型可以尝试
        
        Returns:
            bool: 是否还有更多模型
        """
        return self.current_model_index < len(self.available_models) - 1

    def fix_code_with_llm(self, prompt):
        """非流式修复代码（保持向后兼容）"""
        current_model = self.get_current_model()
        if not current_model:
            logger.error("没有可用的模型")
            return ""

        for attempt in range(self.retry_time):
            try:
                result = self.llm_client.fix_code(prompt, current_model)
                logger.info(f"LLM响应成功，模型: {current_model}，响应长度: {len(result)}")
                return result
            except Exception as e:
                logger.warning(f"LLM请求失败，模型: {current_model}，错误: {e}, retry {attempt+1}/{self.retry_time}")
                time.sleep(self.retry_interval)
        logger.error(f"LLM修复请求多次失败，模型: {current_model}，终止。")
        return ""

    def fix_code_with_llm_stream(self, prompt):
        """流式修复代码，动态显示分析进度"""
        current_model = self.get_current_model()
        if not current_model:
            logger.error("没有可用的模型")
            print("❌ 没有可用的模型", flush=True)
            return ""

        try:
            logger.info(f"开始流式LLM修复，使用模型: {current_model}")
            print(f"🤖 AI分析开始，使用模型: {current_model}...", flush=True)
            
            full_response = ""
            line_count = 0
            
            for chunk in self.llm_client.fix_code_stream(prompt, current_model):
                full_response += chunk
                
                # 计算当前行数（通过换行符计算）
                new_line_count = full_response.count('\n')
                if new_line_count > line_count:
                    line_count = new_line_count
                    # 动态更新分析进度
                    print(f"\r🤖 正在分析第 {line_count} 行代码...", end="", flush=True)
                
                sys.stdout.flush()
            
            # 完成后换行并显示最终结果
            print(f"\n🤖 AI分析完成，模型: {current_model}，共分析 {line_count} 行，响应长度: {len(full_response)}", flush=True)
            logger.info(f"流式LLM响应成功，模型: {current_model}，响应长度: {len(full_response)}")
            return full_response
            
        except Exception as e:
            error_msg = f"流式LLM请求失败，模型: {current_model}，错误: {e}"
            logger.error(error_msg)
            print(f"\n❌ {error_msg}", flush=True)
            return ""

    def fix_code_with_all_models(self, prompt):
        """
        尝试所有可用模型进行代码修复，直到成功或所有模型都失败
        
        Args:
            prompt: 修复提示词
            
        Returns:
            tuple: (success: bool, response: str, used_model: str)
        """
        original_index = self.current_model_index
        
        try:
            # 从当前模型开始尝试所有模型
            while True:
                current_model = self.get_current_model()
                if not current_model:
                    break
                
                logger.info(f"尝试使用模型: {current_model}")
                print(f"🤖 尝试使用模型: {current_model}", flush=True)
                
                response = self.fix_code_with_llm_stream(prompt)
                
                if response and response.strip():
                    logger.info(f"模型 {current_model} 成功生成响应")
                    print(f"✅ 模型 {current_model} 成功生成响应", flush=True)
                    return True, response, current_model
                else:
                    logger.warning(f"模型 {current_model} 返回空响应")
                    print(f"⚠️ 模型 {current_model} 返回空响应", flush=True)
                
                # 切换到下一个模型
                if not self.switch_to_next_model():
                    break
            
            # 所有模型都失败了
            logger.error("所有可用模型都无法生成有效响应")
            print("❌ 所有可用模型都无法生成有效响应", flush=True)
            return False, "", ""
            
        finally:
            # 恢复原始模型索引
            self.current_model_index = original_index

    def analyze_pipeline_logs(self, logs):
        """分析Pipeline日志，使用动态进度显示"""
        current_model = self.get_current_model()
        if not current_model:
            logger.error("没有可用的模型")
            print("❌ 没有可用的模型", flush=True)
            return ""

        try:
            logger.info(f"开始分析Pipeline日志，使用模型: {current_model}")
            print(f"🔍 开始分析Pipeline日志，使用模型: {current_model}...", flush=True)
            
            full_response = ""
            line_count = 0
            
            for chunk in self.llm_client.analyze_pipeline_logs(logs, current_model):
                full_response += chunk
                
                # 计算当前行数
                new_line_count = full_response.count('\n')
                if new_line_count > line_count:
                    line_count = new_line_count
                    print(f"\r🔍 正在分析第 {line_count} 行日志...", end="", flush=True)
                
                sys.stdout.flush()
            
            print(f"\n✅ 日志分析完成，模型: {current_model}，共分析 {line_count} 行", flush=True)
            logger.info(f"Pipeline日志分析完成，模型: {current_model}，响应长度: {len(full_response)}")
            return full_response
            
        except Exception as e:
            error_msg = f"Pipeline日志分析失败，模型: {current_model}，错误: {e}"
            logger.error(error_msg)
            print(f"\n❌ {error_msg}", flush=True)
            return ""
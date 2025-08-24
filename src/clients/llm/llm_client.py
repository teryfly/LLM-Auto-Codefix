# clients/llm/llm_client.py
import requests
import json
import os
from config.config_manager import ConfigManager
from models.llm_models import LLMRequest, LLMResponse
from operations.template.template_manager import TemplateManager
from typing import Iterator, Dict, Any, Optional
from clients.logging.logger import logger

class LLMClient:
    def __init__(self):
        config = ConfigManager.get_config()
        self.api_url = config.services.llm_url
        self.default_models = config.services.get_llm_models()
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-test-key-for-compatibility-Test")
        self.template_manager = TemplateManager()

    def fix_code(self, prompt: str, model: Optional[str] = None) -> str:
        """
        非流式修复代码
        
        Args:
            prompt: 输入提示词
            model: 指定使用的模型，如果不指定则使用默认第一个模型
            
        Returns:
            str: 修复后的代码
        """
        # 明确记录加载 system prompt 的顺序
        logger.debug("Loading system prompt template before non-streaming request")
        system_prompt = self.template_manager.get_system_prompt()

        # 使用指定模型或默认第一个模型
        selected_model = model or self.default_models[0]
        logger.info(f"使用模型: {selected_model}")

        request = LLMRequest(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"Sending non-streaming chat completion request with model: {selected_model}")
        resp = requests.post(
            f"{self.api_url}/chat/completions", 
            json=request.dict(), 
            headers=headers,
            timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        llm_resp = LLMResponse(**data)
        return llm_resp.choices[0].message.content.strip()

    def fix_code_stream(self, prompt: str, model: Optional[str] = None) -> Iterator[str]:
        """
        流式修复代码，不打印内容，只返回流式数据
        
        Args:
            prompt: 输入提示词
            model: 指定使用的模型，如果不指定则使用默认第一个模型
            
        Yields:
            str: 流式内容块
        """
        try:
            # 先加载 system prompt，并打印日志，确保顺序与预期一致
            logger.debug("Loading system prompt template before streaming request")
            system_prompt = self.template_manager.get_system_prompt()

            # 使用指定模型或默认第一个模型
            selected_model = model or self.default_models[0]
            logger.info(f"使用流式模型: {selected_model}")

            request_data = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2048
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 记录即将发起请求的日志
            logger.info(f"正在连接AI服务器，使用模型: {selected_model}")

            with requests.post(
                f"{self.api_url}/chat/completions",
                json=request_data,
                headers=headers,
                stream=True,
                timeout=120
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        decoded = line.decode('utf-8')
                    except Exception:
                        continue
                    if not decoded.startswith('data: '):
                        continue
                    data_str = decoded[6:]  # Remove 'data: ' prefix
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta:
                            yield delta['content']
        except Exception as e:
            logger.error(f"Streaming request failed with model {selected_model}: {e}")
            yield f"Error: {str(e)}"

    def analyze_pipeline_logs(self, logs: str, model: Optional[str] = None) -> Iterator[str]:
        """
        分析Pipeline日志的流式API
        
        Args:
            logs: 日志内容
            model: 指定使用的模型，如果不指定则使用默认第一个模型
            
        Yields:
            str: 流式内容块
        """
        prompt = f"Pipeline日志内容：\n\n{logs}\n\n请分析上述日志中的错误，并提供详细的解决方案。"
        return self.fix_code_stream(prompt, model)

    def get_available_models(self) -> list:
        """
        获取可用的模型列表
        
        Returns:
            list: 模型列表
        """
        return self.default_models.copy()
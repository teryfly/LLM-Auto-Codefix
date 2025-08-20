# clients/llm/llm_client.py

import requests
import json
import os
from config.config_manager import ConfigManager
from models.llm_models import LLMRequest, LLMResponse
from typing import Iterator, Dict, Any

class LLMClient:
    def __init__(self):
        config = ConfigManager.get_config()
        self.api_url = config.services.llm_url
        self.model = config.services.llm_model
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-test-key-for-compatibility-Test")
        self.system_prompt = config.templates.system_prompt

    def fix_code(self, prompt: str) -> str:
        """非流式修复代码"""
        request = LLMRequest(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
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

    def fix_code_stream(self, prompt: str) -> Iterator[str]:
        """流式修复代码"""
        request_data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
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
        
        try:
            with requests.post(
                f"{self.api_url}/chat/completions",
                json=request_data,
                headers=headers,
                stream=True,
                timeout=120
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            yield f"Error: {str(e)}"

    def analyze_pipeline_logs(self, logs: str) -> Iterator[str]:
        """分析Pipeline日志的流式API"""
        prompt = f"Pipeline日志内容：\n\n{logs}\n\n请分析上述日志中的错误，并提供详细的解决方案。"
        return self.fix_code_stream(prompt)
# clients/llm/llm_client.py

import requests
from config.config_manager import ConfigManager
from models.llm_models import LLMRequest, LLMResponse

class LLMClient:
    def __init__(self):
        config = ConfigManager.get_config()
        self.api_url = config.services.llm_url
        self.model = config.services.llm_model

    def fix_code(self, prompt: str) -> str:
        request = LLMRequest(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        resp = requests.post(self.api_url, json=request.dict(), timeout=120)
        resp.raise_for_status()
        data = resp.json()
        llm_resp = LLMResponse(**data)
        return llm_resp.choices[0].message.content.strip()
# clients/llm/llm_formatter.py

from models.llm_models import LLMMessage, LLMRequest

class LLMFormatter:
    @staticmethod
    def build_fix_request(model: str, prompt: str) -> LLMRequest:
        messages = [LLMMessage(role="user", content=prompt)]
        return LLMRequest(model=model, messages=messages)
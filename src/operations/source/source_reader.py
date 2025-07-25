import requests
from typing import Optional
from models.grpc_models import SourceConcatRequest, SourceConcatResponse

class SourceConcatenatorClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip("/") + "/get_project_document"

    def get_project_document(self, project_path: str) -> SourceConcatResponse:
        payload = {"project_path": project_path}
        resp = requests.post(self.api_url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get source document: {resp.text}")
        data = resp.json()
        return SourceConcatResponse(**data)
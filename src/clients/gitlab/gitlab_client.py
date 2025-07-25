# clients/gitlab/gitlab_client.py

import requests
from config.config_manager import ConfigManager

class GitLabClient:
    def __init__(self):
        config = ConfigManager.get_config()
        self.base_url = config.services.gitlab_url.rstrip("/")
        self.token = config.authentication.gitlab_private_token

    def _headers(self):
        return {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.post(url, headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()

    def put(self, endpoint: str, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.put(url, headers=self._headers(), json=data)
        resp.raise_for_status()
        return resp.json()
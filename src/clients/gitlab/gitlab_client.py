# clients/gitlab/gitlab_client.py

import requests
from config.config_manager import ConfigManager
from clients.logging.logger import logger

class GitLabClient:
    def __init__(self):
        config = ConfigManager.get_config()
        # Prefer http URL if provided for API access
        self.base_url = getattr(config.services, "gitlab_http_url", config.services.gitlab_url).rstrip("/")
        self.token = config.authentication.gitlab_private_token

    def _headers(self):
        """
        Prefer PRIVATE-TOKEN header for GitLab, but also include Authorization Bearer
        to maximize compatibility with proxies and some GitLab setups.
        """
        headers = {
            "Content-Type": "application/json",
            "PRIVATE-TOKEN": self.token
        }
        # Some deployments require Bearer; safe to include both
        headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, resp: requests.Response):
        if resp.status_code == 401:
            logger.error("GitLab API unauthorized (401). Check gitlab_private_token and access scope.")
        if resp.status_code == 403:
            logger.error("GitLab API forbidden (403). Token may lack required permissions.")
        if resp.status_code >= 400:
            try:
                logger.error(f"GitLab API error {resp.status_code}: {resp.text}")
            except Exception:
                pass
        resp.raise_for_status()
        # Some endpoints return empty body
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    def get(self, endpoint: str, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        return self._handle_response(resp)

    def post(self, endpoint: str, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.post(url, headers=self._headers(), json=data, timeout=60)
        return self._handle_response(resp)

    def put(self, endpoint: str, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        resp = requests.put(url, headers=self._headers(), json=data, timeout=60)
        return self._handle_response(resp)
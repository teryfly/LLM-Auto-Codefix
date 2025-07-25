# clients/gitlab/project_client.py

from .gitlab_client import GitLabClient
from models.gitlab_models import GitLabProject
from config.config_manager import ConfigManager
from clients.logging.logger import logger
from utils.url_utils import encode_project_path
import sys

class ProjectClient(GitLabClient):
    def get_project_by_name(self, name: str):
        config = ConfigManager.get_config()
        http_url = getattr(config.services, "gitlab_http_url", None)
        if not http_url:
            raise RuntimeError("config.services.gitlab_http_url is required for GitLab API access")
        api_base_url = http_url.rstrip("/")
        self.base_url = api_base_url

        encoded_path = encode_project_path(name)
        api_endpoint = f"api/v4/projects/{encoded_path}"
        logger.info(f"[DEBUG] Will query endpoint: {api_endpoint}")
        logger.info(f"[DEBUG] Full URL: {self.base_url}/{api_endpoint}")

        try:
            project = self.get(api_endpoint)
        except Exception as e:
            logger.error(f"[DEBUG] Exception when querying GitLab API: {e}")
            sys.stdout.flush()
            sys.stderr.flush()
            raise

        if project:
            logger.info(f"[DEBUG] Project found by path: {project.get('path_with_namespace', '')}")
            return GitLabProject(**project)
        logger.info(f"[DEBUG] No project matched for: {name}")
        return None

    def check_project_exists(self, name: str) -> bool:
        return self.get_project_by_name(name) is not None
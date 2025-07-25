# controller/mr_create_controller.py

from clients.gitlab.merge_request_client import MergeRequestClient
from clients.logging.logger import logger

class MrCreateController:
    def __init__(self, config):
        self.config = config
        self.mr_client = MergeRequestClient()

    def create_mr(self, project_id, source_branch="ai", target_branch="dev", title="LLM Auto Merge ai->dev"):
        logger.info(f"Creating merge request: {source_branch} -> {target_branch}")
        mr = self.mr_client.create_merge_request(project_id, source_branch, target_branch, title)
        logger.info(f"Merge request created: {getattr(mr, 'web_url', '')} (iid={mr.iid})")
        return mr
# controller/mr_merge_controller.py

from clients.gitlab.merge_request_client import MergeRequestClient
from clients.logging.logger import logger

class MrMergeController:
    def __init__(self, config):
        self.config = config
        self.mr_client = MergeRequestClient()

    def merge_mr(self, project_id, mr_iid):
        logger.info(f"Merging MR iid={mr_iid} ...")
        merge_result = self.mr_client.merge_mr(project_id, mr_iid)
        logger.info(f"Merge result: {merge_result}")
        return merge_result
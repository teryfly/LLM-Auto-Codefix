# controller/ai_to_git_sync_controller.py

import os
import shutil
from clients.logging.logger import logger

class AiToGitSyncController:
    def __init__(self, config):
        self.config = config

    def sync_ai_to_git(self, local_dir):
        ai_work_dir = self.config.paths.ai_work_dir
        logger.info(f"Copying {ai_work_dir} -> {local_dir}")
        for item in os.listdir(ai_work_dir):
            s = os.path.join(ai_work_dir, item)
            d = os.path.join(local_dir, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
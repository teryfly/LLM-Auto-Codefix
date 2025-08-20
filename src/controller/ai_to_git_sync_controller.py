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
            # 跳过 .git 目录，避免权限/锁定问题
            if item == ".git":
                logger.info("Skipping .git directory during sync")
                continue

            s = os.path.join(ai_work_dir, item)
            d = os.path.join(local_dir, item)

            try:
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            except PermissionError as e:
                logger.error(f"Permission denied while copying {s} -> {d}: {e}")
                raise RuntimeError(f"Permission denied while copying {s}: {e}")
            except Exception as e:
                logger.error(f"Failed to copy {s} -> {d}: {e}")
                raise
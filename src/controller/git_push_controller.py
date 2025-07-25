# controller/git_push_controller.py

import subprocess
from clients.logging.logger import logger
import time

class GitPushController:
    def __init__(self, config):
        self.config = config

    def push_to_ai(self, local_dir, commit_message="llm auto sync", max_retry=3):
        logger.info("Ensuring local 'ai' branch is up-to-date with remote before push")
        for attempt in range(1, max_retry + 1):
            try:
                # 切换到 ai 分支（如无则新建）
                subprocess.run(["git", "checkout", "-B", "ai"], cwd=local_dir, check=True)
                # 拉取远程 ai 分支并 rebase
                subprocess.run(["git", "pull", "--rebase", "origin", "ai"], cwd=local_dir, check=False)
                # add、commit
                subprocess.run(["git", "add", "."], cwd=local_dir, check=True)
                subprocess.run(["git", "commit", "-m", commit_message], cwd=local_dir, check=False)
                # push 到远程 ai 分支
                subprocess.run(["git", "push", "origin", "HEAD:ai"], cwd=local_dir, check=True)
                logger.info("Git push success.")
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Git push error (attempt {attempt}/{max_retry}): {e}")
                if attempt >= max_retry:
                    logger.error("Git push failed after max retries.")
                    raise
                logger.info("Retrying git pull --rebase and push after 3 seconds...")
                time.sleep(3)
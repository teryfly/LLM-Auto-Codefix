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
                # 确保工作区清洁
                subprocess.run(["git", "reset", "--hard"], cwd=local_dir, check=True)
                subprocess.run(["git", "clean", "-fd"], cwd=local_dir, check=True)
                # 强制切换到 ai 分支
                subprocess.run(["git", "checkout", "-B", "ai"], cwd=local_dir, check=True)
                # 获取最新远程状态
                subprocess.run(["git", "fetch", "origin"], cwd=local_dir, check=True)
                # 确保工作区干净后再添加新文件
                subprocess.run(["git", "add", "."], cwd=local_dir, check=True)
                subprocess.run(["git", "commit", "-m", commit_message], cwd=local_dir, check=False)
                # 将本地 ai 分支强制推送到远程
                subprocess.run(["git", "push", "-f", "origin", "HEAD:ai"], cwd=local_dir, check=True)
                logger.info("Git push success.")
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Git push error (attempt {attempt}/{max_retry}): {e}")
                if attempt >= max_retry:
                    logger.error("Git push failed after max retries.")
                    raise
                logger.info("Retrying git push after 3 seconds...")
                time.sleep(3)
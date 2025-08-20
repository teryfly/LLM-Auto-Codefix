# controller/git_push_controller.py
import subprocess
from clients.logging.logger import logger
import time
import os

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
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Git push error (attempt {attempt}/{max_retry}): {e}")
                if attempt >= max_retry:
                    logger.error("Git push failed after max retries.")
                    raise
                logger.info("Retrying git push after 3 seconds...")
                time.sleep(3)

    def commit_and_push_ai_changes(self, commit_message="LLM auto fix"):
        """
        提交修复的代码到 ai_work_dir 对应的本地 git 仓库并推送到远程 ai 分支
        """
        try:
            ai_work_dir = self.config.paths.ai_work_dir
            
            # 检查是否是 git 仓库
            if not os.path.exists(os.path.join(ai_work_dir, '.git')):
                logger.error(f"ai_work_dir {ai_work_dir} 不是 git 仓库")
                print(f"❌ {ai_work_dir} 不是 git 仓库", flush=True)
                return False
            
            logger.info(f"提交 ai_work_dir 的修改: {ai_work_dir}")
            print(f"📤 提交修改到 Git 仓库: {ai_work_dir}", flush=True)
            
            # 切换到 ai 分支
            subprocess.run(["git", "checkout", "-B", "ai"], cwd=ai_work_dir, check=True)
            print("✅ 切换到 ai 分支", flush=True)
            
            # 添加所有修改
            subprocess.run(["git", "add", "."], cwd=ai_work_dir, check=True)
            print("✅ 添加所有修改", flush=True)
            
            # 检查是否有修改需要提交
            result = subprocess.run(["git", "status", "--porcelain"], cwd=ai_work_dir, capture_output=True, text=True)
            if not result.stdout.strip():
                logger.info("没有修改需要提交")
                print("ℹ️ 没有修改需要提交", flush=True)
                return True
            
            # 提交修改
            subprocess.run(["git", "commit", "-m", commit_message], cwd=ai_work_dir, check=True)
            print(f"✅ 提交修改: {commit_message}", flush=True)
            
            # 推送到远程 ai 分支
            subprocess.run(["git", "push", "-f", "origin", "HEAD:ai"], cwd=ai_work_dir, check=True)
            print("✅ 推送到远程 ai 分支", flush=True)
            
            logger.info("成功提交并推送修改")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git 操作失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return False
        except Exception as e:
            error_msg = f"提交和推送失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            return False
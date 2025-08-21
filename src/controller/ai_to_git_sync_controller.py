# controller/ai_to_git_sync_controller.py
import os
import shutil
from clients.logging.logger import logger
class AiToGitSyncController:
    def __init__(self, config):
        self.config = config
    def sync_ai_to_git(self, local_dir):
        """
        将 ai_work_dir 的代码同步到 git_work_dir
        这个方法应该在 git repo 强制更新后调用
        """
        ai_work_dir = self.config.paths.ai_work_dir
        logger.info(f"开始同步 AI 工作目录到 Git 工作目录")
        logger.info(f"源目录 (ai_work_dir): {ai_work_dir}")
        logger.info(f"目标目录 (git_work_dir): {local_dir}")
        print(f"📁 同步 AI 代码: {ai_work_dir} -> {local_dir}", flush=True)
        if not os.path.exists(ai_work_dir):
            error_msg = f"AI 工作目录不存在: {ai_work_dir}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)
        if not os.path.exists(local_dir):
            error_msg = f"Git 工作目录不存在: {local_dir}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)
        try:
            # 获取 ai_work_dir 中的所有文件和目录
            ai_items = os.listdir(ai_work_dir)
            logger.info(f"AI 工作目录包含 {len(ai_items)} 个项目")
            synced_count = 0
            for item in ai_items:
                # 跳过 .git 目录，避免权限/锁定问题
                if item == ".git":
                    logger.info("跳过 .git 目录")
                    continue
                src_path = os.path.join(ai_work_dir, item)
                dst_path = os.path.join(local_dir, item)
                try:
                    # 如果目标已存在，先删除
                    if os.path.exists(dst_path):
                        if os.path.isdir(dst_path):
                            shutil.rmtree(dst_path)
                            logger.debug(f"删除现有目录: {dst_path}")
                        else:
                            os.remove(dst_path)
                            logger.debug(f"删除现有文件: {dst_path}")
                    # 复制新内容
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                        logger.debug(f"复制目录: {src_path} -> {dst_path}")
                    else:
                        shutil.copy2(src_path, dst_path)
                        logger.debug(f"复制文件: {src_path} -> {dst_path}")
                    synced_count += 1
                except PermissionError as e:
                    error_msg = f"权限不足，无法复制 {src_path} -> {dst_path}: {e}"
                    logger.error(error_msg)
                    print(f"❌ {error_msg}", flush=True)
                    raise RuntimeError(error_msg)
                except Exception as e:
                    error_msg = f"复制失败 {src_path} -> {dst_path}: {e}"
                    logger.error(error_msg)
                    print(f"❌ {error_msg}", flush=True)
                    raise RuntimeError(error_msg)
            logger.info(f"成功同步 {synced_count} 个项目从 AI 工作目录到 Git 工作目录")
            print(f"✅ 成功同步 {synced_count} 个项目", flush=True)
        except Exception as e:
            error_msg = f"AI 到 Git 同步失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)
    def verify_sync(self, local_dir):
        """
        验证同步是否成功（可选的验证步骤）
        """
        ai_work_dir = self.config.paths.ai_work_dir
        try:
            # 简单验证：检查主要文件是否存在
            ai_items = [item for item in os.listdir(ai_work_dir) if item != ".git"]
            git_items = [item for item in os.listdir(local_dir) if item != ".git"]
            missing_items = set(ai_items) - set(git_items)
            if missing_items:
                logger.warning(f"Git 工作目录缺少以下项目: {missing_items}")
                print(f"⚠️ Git 工作目录缺少: {missing_items}", flush=True)
                return False
            logger.info("同步验证通过")
            print("✅ 同步验证通过", flush=True)
            return True
        except Exception as e:
            logger.warning(f"同步验证失败: {e}")
            print(f"⚠️ 同步验证失败: {e}", flush=True)
            return False
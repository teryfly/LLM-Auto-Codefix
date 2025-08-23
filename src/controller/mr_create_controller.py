# controller/mr_create_controller.py

from clients.gitlab.merge_request_client import MergeRequestClient
from clients.logging.logger import logger

class MrCreateController:
    def __init__(self, config):
        self.config = config
        self.mr_client = MergeRequestClient()

    def create_mr(self, project_id, source_branch="ai", target_branch="dev", title="LLM Auto Merge ai->dev"):
        logger.info(f"Creating merge request: {source_branch} -> {target_branch}")
        print(f"📝 创建 MR: {source_branch} -> {target_branch}", flush=True)
        
        try:
            mr = self.mr_client.create_merge_request(project_id, source_branch, target_branch, title)
            logger.info(f"Merge request created successfully: {getattr(mr, 'web_url', '')} (iid={mr.iid})")
            print(f"✅ MR 创建成功: {getattr(mr, 'web_url', '')} (iid={mr.iid})", flush=True)
            return mr
            
        except Exception as e:
            logger.error(f"Failed to create merge request: {e}")
            print(f"❌ MR 创建失败: {e}", flush=True)
            raise

    def close_existing_open_mrs(self, project_id, source_branch="ai"):
        """
        关闭指定源分支的所有开放 MR
        
        Args:
            project_id: 项目 ID
            source_branch: 源分支名称
            
        Returns:
            int: 关闭的 MR 数量
        """
        logger.info(f"Checking for existing open MRs from branch {source_branch}")
        print(f"🔍 检查来自分支 {source_branch} 的开放 MR", flush=True)
        
        try:
            # 获取所有开放的 MR
            open_mrs = self.mr_client.list_open_merge_requests(project_id, source_branch)
            
            if not open_mrs:
                logger.info("No existing open MRs found")
                print("ℹ️ 未发现现有的开放 MR", flush=True)
                return 0
            
            closed_count = 0
            for mr in open_mrs:
                logger.info(f"Found open MR: {mr.iid} - {mr.title}")
                print(f"🔍 发现开放 MR: {mr.iid} - {mr.title}", flush=True)
                
                if self.mr_client.close_merge_request(project_id, mr.iid):
                    closed_count += 1
                    logger.info(f"Successfully closed MR {mr.iid}")
                    print(f"✅ 成功关闭 MR {mr.iid}", flush=True)
                else:
                    logger.warning(f"Failed to close MR {mr.iid}")
                    print(f"⚠️ 关闭 MR {mr.iid} 失败", flush=True)
            
            logger.info(f"Closed {closed_count} out of {len(open_mrs)} open MRs")
            print(f"📊 关闭了 {closed_count}/{len(open_mrs)} 个开放 MR", flush=True)
            return closed_count
            
        except Exception as e:
            logger.error(f"Error while closing existing MRs: {e}")
            print(f"❌ 关闭现有 MR 时出错: {e}", flush=True)
            return 0

    def create_mr_with_conflict_resolution(self, project_id, source_branch="ai", target_branch="dev", title="LLM Auto Merge ai->dev"):
        """
        创建 MR，如果遇到冲突则自动关闭现有 MR 后重试
        
        Args:
            project_id: 项目 ID
            source_branch: 源分支
            target_branch: 目标分支
            title: MR 标题
            
        Returns:
            MergeRequest: 创建的 MR 对象
        """
        logger.info(f"Creating merge request with conflict resolution: {source_branch} -> {target_branch}")
        print(f"📝 创建 MR (含冲突解决): {source_branch} -> {target_branch}", flush=True)
        
        try:
            # 首先尝试直接创建 MR
            return self.create_mr(project_id, source_branch, target_branch, title)
            
        except Exception as e:
            error_msg = str(e)
            
            # 检查是否是因为已存在开放 MR 导致的冲突
            if "409" in error_msg or "already exists" in error_msg.lower():
                logger.info("Detected existing MR conflict, attempting to resolve")
                print("🔧 检测到 MR 冲突，尝试解决", flush=True)
                
                # 尝试关闭现有的开放 MR
                closed_count = self.close_existing_open_mrs(project_id, source_branch)
                
                if closed_count > 0:
                    logger.info(f"Closed {closed_count} existing MRs, retrying creation")
                    print(f"🔄 已关闭 {closed_count} 个现有 MR，重新尝试创建", flush=True)
                    
                    # 重新尝试创建 MR
                    return self.create_mr(project_id, source_branch, target_branch, title)
                else:
                    logger.error("No MRs were closed, cannot resolve conflict")
                    print("❌ 未能关闭任何 MR，无法解决冲突", flush=True)
                    raise
            else:
                # 其他类型的错误，直接抛出
                raise
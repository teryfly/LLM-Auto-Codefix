# controller/mr_merge_controller.py
from clients.gitlab.merge_request_client import MergeRequestClient
from clients.logging.logger import logger
class MrMergeController:
    def __init__(self, config):
        self.config = config
        self.mr_client = MergeRequestClient()
    def merge_mr(self, project_id, mr_iid):
        """合并MR，提供友好的错误处理"""
        logger.info(f"Attempting to merge MR iid={mr_iid} ...")
        try:
            merge_result = self.mr_client.merge_mr(project_id, mr_iid)
            logger.info(f"Merge successful: {merge_result}")
            print(f"✅ Merge Request {mr_iid} has been successfully merged!")
            return merge_result
        except ValueError as e:
            # 这些是友好的错误消息，不需要重新抛出
            error_msg = str(e)
            logger.warning(f"Merge not possible for MR {mr_iid}: {error_msg}")
            print(f"⚠️  Merge Request {mr_iid} cannot be merged: {error_msg}")
            # 根据错误类型提供建议
            if "no changes" in error_msg.lower():
                print("💡 Suggestion: Check if there are actual differences between the source and target branches.")
            elif "conflicts" in error_msg.lower():
                print("💡 Suggestion: Resolve the merge conflicts in GitLab or locally, then try again.")
            elif "work in progress" in error_msg.lower():
                print("💡 Suggestion: Remove the WIP status from the merge request and try again.")
            elif "already merged" in error_msg.lower():
                print("✅ The merge request has already been completed.")
            # 返回一个表示无法合并的结果，而不是抛出异常
            return {
                "status": "cannot_merge",
                "reason": error_msg,
                "merge_successful": False
            }
        except Exception as e:
            # 其他未预期的错误
            logger.error(f"Unexpected error during merge: {e}")
            print(f"❌ Unexpected error occurred while merging MR {mr_iid}: {str(e)}")
            raise
# controller/main_workflow/step_merge_mr.py
import time
from controller.mr_merge_controller import MrMergeController
from clients.logging.logger import logger
from clients.gitlab.pipeline_client import PipelineClient
def merge_mr_and_wait_pipeline(config, project_info, mr):
    mr_merge_ctrl = MrMergeController(config)
    pipeline_client = PipelineClient()
    print("准备部署中，请等待...")
    time.sleep(3)  # 给 GitLab 几秒触发新 pipeline
    logger.info(f"Attempting to merge MR iid={mr.iid}")
    merge_result = mr_merge_ctrl.merge_mr(project_info["project_id"], mr.iid)
    # 检查合并结果
    if isinstance(merge_result, dict) and merge_result.get("status") == "cannot_merge":
        # 合并失败，但这是预期的情况（比如没有变化）
        logger.warning(f"MR {mr.iid} could not be merged: {merge_result.get('reason')}")
        print(f"⚠️  Merge step skipped: {merge_result.get('reason')}")
        # 将错误信息存储到project_info中，供后续步骤使用
        project_info["merge_skipped"] = True
        project_info["merge_skip_reason"] = merge_result.get('reason')
        # 不查找新的pipeline，因为没有发生合并
        return
    # 合并成功，等待新的pipeline
    time.sleep(5)  # 等待 GitLab pipeline 创建完毕
    pipelines = pipeline_client.list_pipelines(project_info["project_id"], ref="dev")
    if not pipelines:
        logger.warning("Merge 后未发现新的 pipeline，可能需要更长时间等待")
        print("⚠️  No new pipeline detected after merge. This may be normal for some projects.")
        project_info["merged_pipeline_id"] = None
    else:
        merged_pipeline = pipelines[0]
        project_info["merged_pipeline_id"] = merged_pipeline.id
        logger.info(f"Found post-merge pipeline: {merged_pipeline.id}")
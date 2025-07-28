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
    logger.info(f"Merging MR iid={mr.iid}")
    mr_merge_ctrl.merge_mr(project_info["project_id"], mr.iid)

    time.sleep(5)  # 等待 GitLab pipeline 创建完毕
    pipelines = pipeline_client.list_pipelines(project_info["project_id"], ref="dev")
    if not pipelines:
        raise Exception("Merge 后未发现新的 pipeline")
    
    merged_pipeline = pipelines[0]
    project_info["merged_pipeline_id"] = merged_pipeline.id

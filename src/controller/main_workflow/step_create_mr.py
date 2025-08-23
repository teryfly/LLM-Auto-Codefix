# controller/main_workflow/step_create_mr.py

import time
import datetime
from controller.mr_create_controller import MrCreateController
from clients.gitlab.pipeline_client import PipelineClient
from clients.logging.logger import logger

def create_merge_request(config, project_info):
    mr_ctrl = MrCreateController(config)
    pipeline_client = PipelineClient()

    now = datetime.datetime.now().strftime("%H%M%S")
    mr_title = f"LLM Auto Merge ai->dev [{now}]"
    
    logger.info("Starting merge request creation with automatic conflict resolution")
    print("📝 开始创建 MR（自动处理冲突）", flush=True)
    
    # 使用带冲突解决的创建方法
    mr = mr_ctrl.create_mr_with_conflict_resolution(
        project_info["project_id"], 
        "ai", 
        "dev", 
        mr_title
    )

    print("准备编译中，请等待...")
    time.sleep(10)

    # 获取 MR 创建后的 pipeline
    pipelines = pipeline_client.list_pipelines(project_info["project_id"], ref="ai")
    if not pipelines:
        logger.error("No pipeline found for 'ai' branch.")
        raise Exception("No pipeline found for 'ai' branch.")
    project_info["pipeline_id"] = pipelines[0].id

    logger.info(f"MR created successfully with pipeline {pipelines[0].id}")
    print(f"✅ MR 创建完成，Pipeline ID: {pipelines[0].id}", flush=True)
    
    return mr
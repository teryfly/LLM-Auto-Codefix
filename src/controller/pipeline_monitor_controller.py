# controller/pipeline_monitor_controller.py

import time
from clients.gitlab.job_client import JobClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.logging.logger import logger

PIPELINE_SUCCESS_STATES = {"success", "skipped", "canceled"}
PIPELINE_RUNNING_STATES = {"running", "pending", "created", "scheduled"}
PIPELINE_FAILED_STATES = {"failed"}
PIPELINE_MANUAL_STATES = {"manual"}

class PipelineMonitorController:
    """
    负责监控 GitLab pipeline 状态，打印和记录每个job的状态变化
    """
    def __init__(self, config):
        self.config = config
        self.job_client = JobClient()
        self.pipeline_client = PipelineClient()
        self.interval = config.timeout.pipeline_check_interval
        
    def monitor(self, project_id, pipeline_id):
        last_statuses = {}
        dot_counters = {}
        while True:
            jobs = self.job_client.list_jobs(project_id, pipeline_id)
            all_status = [j.status for j in jobs]
            for job in jobs:
                job_key = f"{job.stage}-{job.name}" if job.stage else job.name
                current_status = job.status
                previous_status = last_statuses.get(job_key)
                if previous_status != current_status:
                    # 状态变更，换行输出变更信息
                    print(f"\n[Job: {job.name}] Stage: {job.stage} | Status: {current_status}")
                    logger.info(f"[Job: {job.name}] Status changed: {previous_status} -> {current_status}")
                    last_statuses[job_key] = current_status
                    dot_counters[job_key] = 0
                else:
                    # 正常只输出点，不换行
                    print(".", end="", flush=True)
                    dot_counters[job_key] = dot_counters.get(job_key, 0) + 1
                    # 不再主动换行，除非状态变更
            if all(s in PIPELINE_SUCCESS_STATES for s in all_status):
                print("\n[INFO] Pipeline所有任务完成（成功/跳过/取消），结束。")
                logger.info("All jobs succeeded/skipped/canceled.")
                return "success", jobs
            if any(s in PIPELINE_MANUAL_STATES for s in all_status):
                print("\n[INFO] Pipeline等待人工操作，等待中...")
                logger.info("Pipeline has manual state, waiting...")
                time.sleep(self.interval)
                continue
            if any(s in PIPELINE_FAILED_STATES for s in all_status):
                print("\n[WARN] Pipeline有任务失败，进入修复流程。")
                logger.info("Pipeline detected failed job.")
                return "failed", jobs
            if any(s in PIPELINE_RUNNING_STATES for s in all_status):
                time.sleep(self.interval)
                continue
            time.sleep(self.interval)

    def get_latest_pipeline(self, project_id, ref="ai"):
        """
        获取指定分支的最新 Pipeline
        """
        try:
            logger.info(f"获取 {ref} 分支的最新 Pipeline")
            pipeline = self.pipeline_client.get_latest_pipeline(project_id, ref)
            if pipeline:
                logger.info(f"找到最新 Pipeline: {pipeline.id}, 状态: {pipeline.status}")
                return {"id": pipeline.id, "status": pipeline.status}
            else:
                logger.warning(f"未找到 {ref} 分支的 Pipeline")
                return None
        except Exception as e:
            logger.error(f"获取最新 Pipeline 失败: {e}")
            return None
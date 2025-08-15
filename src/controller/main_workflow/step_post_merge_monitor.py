# controller/main_workflow/step_post_merge_monitor.py
import time
from clients.gitlab.job_client import JobClient
from clients.logging.logger import logger
SUCCESS_STATES = {"success", "skipped", "canceled"}
RUNNING_STATES = {"running", "pending", "created", "scheduled"}
FAILED_STATES = {"failed"}
MANUAL_STATES = {"manual"}
def monitor_post_merge_pipeline(config, project_info):
    # 检查是否合并失败
    if project_info.get("merge_failed", False):
        error_reason = project_info.get("merge_error", "Unknown merge error")
        print(f"\n[ERROR] 合并步骤失败: {error_reason}")
        print("[ERROR] 后合并监控步骤无法执行")
        logger.error(f"Post-merge monitoring cannot proceed because merge failed: {error_reason}")
        raise RuntimeError(f"Post-merge monitoring failed due to merge error: {error_reason}")
    # 检查是否跳过了合并步骤（这种情况现在不应该发生，因为合并失败会抛出异常）
    if project_info.get("merge_skipped", False):
        reason = project_info.get("merge_skip_reason", "Unknown reason")
        print(f"\n[INFO] 合并步骤已跳过: {reason}")
        print("[INFO] 后合并监控步骤也将跳过")
        logger.info(f"Post-merge monitoring skipped because merge was skipped: {reason}")
        return
    # 检查是否有pipeline ID
    if not project_info.get("merged_pipeline_id"):
        print(f"\n[INFO] 没有检测到合并后的Pipeline，跳过监控步骤")
        logger.info("No post-merge pipeline detected, skipping monitoring")
        return
    job_client = JobClient()
    project_id = project_info["project_id"]
    pipeline_id = project_info["merged_pipeline_id"]
    print(f"\n[INFO] 开始监控合并后部署 Pipeline (ID: {pipeline_id})")
    last_statuses = {}
    dot_count = {}
    while True:
        try:
            jobs = job_client.list_jobs(project_id, pipeline_id)
            statuses = [job.status for job in jobs]
            for job in jobs:
                key = f"{job.stage}-{job.name}" if job.stage else job.name
                status = job.status
                prev = last_statuses.get(key)
                if prev != status:
                    print(f"\n[Stage: {job.stage}] Job: {job.name} | Status: {status}")
                    logger.info(f"[Post-Merge Job] {job.name} ({job.stage}) changed: {prev} -> {status}")
                    last_statuses[key] = status
                    dot_count[key] = 0
                else:
                    print(".", end="", flush=True)
                    dot_count[key] = dot_count.get(key, 0) + 1
            if all(s in SUCCESS_STATES for s in statuses):
                print("\n[✅ 合并后部署完成]")
                break
            if any(s in FAILED_STATES for s in statuses):
                print("\n[❌ 合并后部署失败]")
                break
            if any(s in MANUAL_STATES for s in statuses):
                print("\n[⏸️ 等待人工操作]")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error monitoring post-merge pipeline: {e}")
            print(f"\n[❌ 监控出错: {str(e)}]")
            break
# 确保 monitor_post_merge_pipeline 可被 import
__all__ = ["monitor_post_merge_pipeline"]
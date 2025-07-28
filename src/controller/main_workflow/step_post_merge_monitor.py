# controller/main_workflow/step_post_merge_monitor.py

import time
from clients.gitlab.job_client import JobClient
from clients.logging.logger import logger

SUCCESS_STATES = {"success", "skipped", "canceled"}
RUNNING_STATES = {"running", "pending", "created", "scheduled"}
FAILED_STATES = {"failed"}
MANUAL_STATES = {"manual"}

def monitor_post_merge_pipeline(config, project_info):
    job_client = JobClient()
    project_id = project_info["project_id"]
    pipeline_id = project_info["merged_pipeline_id"]

    print(f"\n[INFO] 开始监控合并后部署 Pipeline (ID: {pipeline_id})")

    last_statuses = {}
    dot_count = {}

    while True:
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
                dot_count[key] += 1
                if dot_count[key] % 10 == 0:
                    print("", end="\n", flush=True)

        if all(s in SUCCESS_STATES for s in statuses):
            print("\n[✅ 合并后部署完成]")
            break
        if any(s in FAILED_STATES for s in statuses):
            print("\n[❌ 合并后部署失败]")
            break
        if any(s in MANUAL_STATES for s in statuses):
            print("\n[⏸️ 等待人工操作]")
        time.sleep(2)

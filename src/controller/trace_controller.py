# controller/trace_controller.py

from clients.gitlab.job_client import JobClient
from clients.logging.logger import logger

class TraceController:
    def __init__(self):
        self.job_client = JobClient()

    def get_failed_trace(self, project_id, jobs):
        for job in jobs:
            if job.status == "failed":
                trace = self.job_client.get_job_trace(project_id, job.id)
                logger.info(f"TRACE CONTENT: {trace}")
                print("测试未通过，正在检查代码...")
                return trace
        logger.warning("No failed job trace found.")
        return ""
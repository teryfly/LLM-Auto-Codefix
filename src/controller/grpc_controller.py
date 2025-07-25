# controller/grpc_controller.py

from clients.grpc.grpc_client import GrpcClient
from clients.logging.logger import logger

class GrpcController:
    def __init__(self, config):
        self.grpc_client = GrpcClient()
        self.project_id = None

    def run_plan(self, plan_text, project_id):
        # 伪代码示意，具体依赖真实grpc定义
        # feedbacks = self.grpc_client.run_plan(plan_text=plan_text, project_id=project_id)
        # for feedback in feedbacks:
        #     print(f"[GRPC-Feedback]: {feedback.output} {feedback.error}")
        #     logger.info(f"[GRPC-Feedback]: {feedback.output} {feedback.error}")
        # if feedbacks[-1].exit_code == 0:
        #     return True
        # else:
        #     return False
        # 以下为mock实现
        print(f"[GRPC] RunPlan for {project_id} ...")
        logger.info(f"[GRPC] RunPlan for {project_id} ...")
        # 假装成功
        return True
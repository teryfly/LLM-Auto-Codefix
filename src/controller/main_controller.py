# controller/main_controller.py

import datetime
import time
from controller.input_project_controller import InputProjectController
from controller.repo_sync_controller import RepoSyncController
from controller.ai_to_git_sync_controller import AiToGitSyncController
from controller.git_push_controller import GitPushController
from controller.mr_create_controller import MrCreateController
from controller.mr_merge_controller import MrMergeController
from controller.pipeline_monitor_controller import PipelineMonitorController
from controller.trace_controller import TraceController
from controller.source_code_controller import SourceCodeController
from controller.prompt_controller import PromptController
from controller.llm_controller import LLMController
from controller.grpc_controller import GrpcController
from controller.loop_controller import LoopController
from clients.gitlab.pipeline_client import PipelineClient
from clients.logging.logger import logger

class MainController:
    def __init__(self, config):
        self.config = config
        self.input_project_ctrl = InputProjectController()
        self.repo_sync_ctrl = RepoSyncController(config)
        self.ai_to_git_sync_ctrl = AiToGitSyncController(config)
        self.git_push_ctrl = GitPushController(config)
        self.mr_create_ctrl = MrCreateController(config)
        self.mr_merge_ctrl = MrMergeController(config)
        self.pipeline_monitor = PipelineMonitorController(config)
        self.trace_ctrl = TraceController()
        self.source_code_ctrl = SourceCodeController(config)
        self.prompt_ctrl = PromptController()
        self.llm_ctrl = LLMController(config)
        self.grpc_ctrl = GrpcController(config)
        self.loop_ctrl = LoopController(config)
        self.pipeline_client = PipelineClient()

    def run(self):
        project_name, encoded_path, project, project_id = self.input_project_ctrl.get_project_info()
        local_dir = self.repo_sync_ctrl.sync_repo(project_name)
        self.ai_to_git_sync_ctrl.sync_ai_to_git(local_dir)
        self.git_push_ctrl.push_to_ai(local_dir, commit_message="llm auto sync")

        now = datetime.datetime.now().strftime("%H%M%S")
        mr_title = f"LLM Auto Merge ai->dev [{now}]"
        mr = self.mr_create_ctrl.create_mr(
            project_id,
            source_branch="ai",
            target_branch="dev",
            title=mr_title
        )

        print("编译中，请等待...")
        for sec in range(5, 0, -1):
            print(f"请等待 {sec} 秒...", end="\r")
            time.sleep(1)
        print(" " * 32, end="\r")

        # 获取最新 pipeline
        pipelines = self.pipeline_client.list_pipelines(project_id, ref="ai")
        if not pipelines:
            logger.error("No pipeline found for the branch 'ai'.")
            raise Exception("No pipeline found for the branch 'ai'.")
        pipeline_id = pipelines[0].id

        def loop_body(debug_idx):
            status, jobs = self.pipeline_monitor.monitor(project_id, pipeline_id)
            if status == "success":
                return True
            if status == "failed":
                trace = self.trace_ctrl.get_failed_trace(project_id, jobs)
                source_code = self.source_code_ctrl.get_failed_source_codes(project_name)
                prompt = self.prompt_ctrl.build_fix_prompt(trace, source_code)
                fixed_code = self.llm_ctrl.fix_code_with_llm(prompt)
                ok = self.grpc_ctrl.run_plan(fixed_code, project_name)
                return ok
            for sec in range(5, 0, -1):
                print(f"[下一轮尝试] 请等待 {sec} 秒...", end="\r")
                time.sleep(1)
            print(" " * 32, end="\r")
            return False

        self.loop_ctrl.run_with_timeout(loop_body)
        
        #  执行合并
        self.mr_merge_ctrl.merge_mr(project_id, mr.iid)
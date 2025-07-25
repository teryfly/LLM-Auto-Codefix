from typing import Optional
from clients.gitlab.project_client import ProjectClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.gitlab.job_client import JobClient
from clients.gitlab.merge_request_client import MergeRequestClient
from operations.git.git_manager import GitManager
from operations.file.file_manager import FileManager
from operations.template.prompt_builder import PromptBuilder
from operations.source.source_reader import SourceConcatenatorClient
from clients.llm.llm_client import LLMClient
from utils.helpers import prompt_user, exit_with_error
from utils.exceptions import ProjectNotFoundError, RetryLimitExceeded, ManualInterventionRequired
from models.constants import PIPELINE_SUCCESS_STATES, PIPELINE_FAILURE_STATES, PIPELINE_WAITING_STATES, PIPELINE_RUNNING_STATES
from clients.logging.logger import logger
import time

class MainController:
    def __init__(self, config):
        self.config = config
        self.project_client = ProjectClient()
        self.pipeline_client = PipelineClient()
        self.job_client = JobClient()
        self.mr_client = MergeRequestClient()
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient()
        self.source_concat = SourceConcatenatorClient(config.services.gitlab_url)
        self.file_manager = FileManager()
        self.git_manager: Optional[GitManager] = None
        self.project = None

    def run(self):
        # Step 1: 输入并校验项目
        project_name = input("Enter the GitLab project name (e.g. group/myproject): ").strip()
        logger.info(f"Checking for project: {project_name}")
        project = self.project_client.get_project_by_name(project_name)
        if not project:
            logger.error(f"Project '{project_name}' not found.")
            if not prompt_user(f"Project '{project_name}' not found. Continue anyway?"):
                raise ProjectNotFoundError(f"Project '{project_name}' not found.")
        else:
            logger.info(f"Project '{project_name}' found (or proceeding per user input).")
        self.project = project

        # Step 2: 仓库拉取与分支准备
        repo_url = f"{self.config.services.gitlab_url}/{project.path_with_namespace}.git"
        self.git_manager = GitManager(repo_url, self.config.paths.git_work_dir)
        self.git_manager.ensure_repository()
        branch_name = f"llm-auto-fix-{int(time.time())}"
        self.git_manager.create_and_checkout_branch(branch_name)

        # Step 3: 文件同步（AI工作区、源代码工作区同步，可自定义）
        # 这里可以实现AI工作区到git分支的同步，例如
        # self.file_manager.sync_files(self.config.paths.ai_work_dir, self.config.paths.git_work_dir)
        # 也可以加入自定义同步逻辑

        # Step 4: 推送代码至新分支
        commit_msg = "LLM auto fix: initial commit"
        if self.git_manager.sync_and_commit(commit_msg):
            self.git_manager.push_branch(branch_name)

        # Step 5: 创建 Merge Request
        mr = self.mr_client.create_merge_request(project.id, branch_name, "master", f"LLM Auto Fix {branch_name}")
        logger.info(f"Created MR: {mr.web_url}")

        # Step 6: 创建并监控 Pipeline
        pipeline = self.pipeline_client.create_pipeline(project.id, branch_name)
        logger.info(f"Created pipeline: {pipeline.web_url}")

        retry_time = 0
        debug_cycle = 0
        while debug_cycle < self.config.retry_config.debug_max_time:
            logger.info(f"Monitoring pipeline (iteration {debug_cycle+1}) ...")
            while retry_time < self.config.retry_config.retry_max_time:
                pipeline = self.pipeline_client.get_pipeline(project.id, pipeline.id)
                logger.info(f"Pipeline status: {pipeline.status}")
                if pipeline.status in PIPELINE_SUCCESS_STATES:
                    logger.info("Pipeline succeeded. Workflow complete.")
                    print("\n[FINISH] CI/CD pipeline succeeded.\n")
                    return
                elif pipeline.status in PIPELINE_FAILURE_STATES:
                    logger.warning("Pipeline failed. Entering code fix cycle.")
                    break
                elif pipeline.status in PIPELINE_WAITING_STATES:
                    print("[INFO] Pipeline waiting for manual intervention. Please resolve in GitLab UI.")
                    raise ManualInterventionRequired("Pipeline entered manual state.")
                elif pipeline.status in PIPELINE_RUNNING_STATES:
                    print(f"[INFO] Pipeline running. Checking again in {self.config.retry_config.retry_interval_time} seconds ...")
                else:
                    logger.warning(f"Unknown pipeline status: {pipeline.status}")
                time.sleep(self.config.retry_config.retry_interval_time)
                retry_time += 1
            else:
                logger.error("Pipeline did not complete in expected retries. Exiting.")
                raise RetryLimitExceeded("Pipeline execution exceeded retry limit.")

            # Step 7: 获取失败 Job 和 Trace
            jobs = self.job_client.list_jobs(project.id, pipeline.id)
            failed_job = next((j for j in jobs if j.status in PIPELINE_FAILURE_STATES), None)
            if not failed_job:
                logger.error("No failed job found in failed pipeline.")
                raise Exception("No failed job trace available.")
            trace = self.job_client.get_job_trace(project.id, failed_job.id)
            logger.info(f"Collected failed job trace for job: {failed_job.name}")

            # Step 8: 获取项目源码（调用 source code concatenator）
            concat_result = self.source_concat.get_project_document(self.config.paths.git_work_dir)
            source_code = concat_result.document

            # Step 9: 构造 LLM 修复 Prompt
            prompt = self.prompt_builder.build_fix_bug_prompt(trace, source_code)
            logger.info("Built prompt for LLM code fix.")

            # Step 10: LLM 进行代码修复
            fixed_code = self.llm_client.fix_code(prompt)
            logger.info("LLM returned fixed code.")

            # Step 11: 覆盖 AI 工作目录源码，并同步到 git 分支
            fixed_code_file = f"{self.config.paths.ai_work_dir}/llm_fixed_code.py"
            with open(fixed_code_file, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            self.file_manager.sync_files(self.config.paths.ai_work_dir, self.config.paths.git_work_dir)
            logger.info("Synchronized fixed code files to git work dir.")

            # Step 12: 推送修复后的代码
            commit_msg = f"LLM auto fix: attempt #{debug_cycle+1}"
            if self.git_manager.sync_and_commit(commit_msg):
                self.git_manager.push_branch(branch_name)
                pipeline = self.pipeline_client.create_pipeline(project.id, branch_name)
                logger.info(f"Triggered new pipeline: {pipeline.web_url}")
            else:
                logger.warning("No changes detected for new commit.")

            debug_cycle += 1
            retry_time = 0

        logger.error("Exceeded maximum code fix debug cycles. Manual intervention required.")
        print("\n[FAIL] All debug cycles exhausted. Please check logs and fix manually.\n")
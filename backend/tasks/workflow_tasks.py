import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from models.web.api_models import WorkflowStartRequest
from models.web.workflow_models import WorkflowState, WorkflowStep, StepStatus
from tasks.task_base import BaseTask

logger = logging.getLogger("workflow_tasks")

class PrepareProjectTask(BaseTask):
    """Task for project preparation step"""

    def __init__(self, config: AppConfig, session_id: str, request: WorkflowStartRequest):
        super().__init__(f"prepare_project_{session_id}", "Prepare Project")
        self.config = config
        self.session_id = session_id
        self.request = request

    async def execute(self) -> Dict[str, Any]:
        """Execute project preparation"""
        try:
            self.add_log("Starting project preparation")

            # Import and use existing controller logic
            from controller.main_workflow.step_prepare_project import prepare_project

            # Execute project preparation
            project_info = prepare_project(self.config)

            self.add_log(f"Project prepared: {project_info.get('project_name', 'Unknown')}")
            return project_info

        except Exception as e:
            self.add_log(f"Project preparation failed: {e}")
            raise

class CreateMergeRequestTask(BaseTask):
    """Task for creating merge request"""

    def __init__(self, config: AppConfig, session_id: str, project_info: Dict[str, Any]):
        super().__init__(f"create_mr_{session_id}", "Create Merge Request")
        self.config = config
        self.session_id = session_id
        self.project_info = project_info

    async def execute(self) -> Dict[str, Any]:
        """Execute merge request creation"""
        try:
            self.add_log("Creating merge request")

            from controller.main_workflow.step_create_mr import create_merge_request

            # Execute MR creation
            mr = create_merge_request(self.config, self.project_info)

            self.add_log(f"Merge request created: {getattr(mr, 'web_url', 'Unknown')}")
            return {"merge_request": mr, "project_info": self.project_info}

        except Exception as e:
            self.add_log(f"Merge request creation failed: {e}")
            raise

class DebugLoopTask(BaseTask):
    """Task for debug loop execution"""

    def __init__(self, config: AppConfig, session_id: str, project_info: Dict[str, Any], mr: Any):
        super().__init__(f"debug_loop_{session_id}", "Debug Loop")
        self.config = config
        self.session_id = session_id
        self.project_info = project_info
        self.mr = mr

    async def execute(self) -> Dict[str, Any]:
        """Execute debug loop"""
        try:
            self.add_log("Starting debug loop")

            from controller.main_workflow.step_debug_loop import run_debug_loop

            # Execute debug loop
            run_debug_loop(self.config, self.project_info, self.mr)

            self.add_log("Debug loop completed successfully")
            return {"project_info": self.project_info, "merge_request": self.mr}

        except Exception as e:
            self.add_log(f"Debug loop failed: {e}")
            raise

class MergeMRTask(BaseTask):
    """Task for merging MR and waiting for pipeline"""

    def __init__(self, config: AppConfig, session_id: str, project_info: Dict[str, Any], mr: Any):
        super().__init__(f"merge_mr_{session_id}", "Merge MR")
        self.config = config
        self.session_id = session_id
        self.project_info = project_info
        self.mr = mr

    async def execute(self) -> Dict[str, Any]:
        """Execute MR merge"""
        try:
            self.add_log("Merging MR and waiting for pipeline")

            from controller.main_workflow.step_merge_mr import merge_mr_and_wait_pipeline

            # Execute MR merge
            merge_mr_and_wait_pipeline(self.config, self.project_info, self.mr)

            self.add_log("MR merged successfully")
            return {"project_info": self.project_info, "merge_request": self.mr}

        except Exception as e:
            self.add_log(f"MR merge failed: {e}")
            raise

class PostMergeMonitorTask(BaseTask):
    """Task for post-merge monitoring"""

    def __init__(self, config: AppConfig, session_id: str, project_info: Dict[str, Any]):
        super().__init__(f"post_merge_monitor_{session_id}", "Post-Merge Monitor")
        self.config = config
        self.session_id = session_id
        self.project_info = project_info

    async def execute(self) -> Dict[str, Any]:
        """Execute post-merge monitoring"""
        try:
            self.add_log("Starting post-merge monitoring")

            from controller.main_workflow.step_post_merge_monitor import monitor_post_merge_pipeline

            # Execute post-merge monitoring
            monitor_post_merge_pipeline(self.config, self.project_info)

            self.add_log("Post-merge monitoring completed")

            # Extract deployment URL if available
            deployment_url = self._extract_deployment_url()

            return {
                "project_info": self.project_info,
                "deployment_url": deployment_url,
                "status": "completed"
            }

        except Exception as e:
            self.add_log(f"Post-merge monitoring failed: {e}")
            raise

    def _extract_deployment_url(self) -> Optional[str]:
        """Extract deployment URL from project info"""
        # This would extract the actual deployment URL
        # For now, return a placeholder
        project_name = self.project_info.get("project_name", "unknown")
        return f"https://deploy.example.com/{project_name.replace('/', '-')}"
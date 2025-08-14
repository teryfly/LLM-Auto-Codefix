import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from controller.main_controller import MainController

logger = logging.getLogger("legacy_adapter")

class LegacyControllerAdapter:
    """Adapter to integrate existing controllers with web API"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.main_controller = None

    def initialize_controller(self) -> MainController:
        """Initialize the main controller"""
        if self.main_controller is None:
            self.main_controller = MainController(self.config)
        return self.main_controller

    def execute_full_workflow(self) -> Dict[str, Any]:
        """Execute the complete workflow using existing controller"""
        try:
            controller = self.initialize_controller()

            # Execute the main workflow
            controller.run()

            return {
                "status": "completed",
                "message": "Workflow executed successfully"
            }

        except Exception as e:
            logger.error(f"Legacy workflow execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def prepare_project_step(self) -> Dict[str, Any]:
        """Execute project preparation step"""
        try:
            from controller.main_workflow.step_prepare_project import prepare_project
            project_info = prepare_project(self.config)

            return {
                "status": "completed",
                "project_info": project_info
            }

        except Exception as e:
            logger.error(f"Project preparation failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def create_mr_step(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute merge request creation step"""
        try:
            from controller.main_workflow.step_create_mr import create_merge_request
            mr = create_merge_request(self.config, project_info)

            return {
                "status": "completed",
                "merge_request": mr,
                "project_info": project_info
            }

        except Exception as e:
            logger.error(f"MR creation failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def debug_loop_step(self, project_info: Dict[str, Any], mr: Any) -> Dict[str, Any]:
        """Execute debug loop step"""
        try:
            from controller.main_workflow.step_debug_loop import run_debug_loop
            run_debug_loop(self.config, project_info, mr)

            return {
                "status": "completed",
                "project_info": project_info,
                "merge_request": mr
            }

        except Exception as e:
            logger.error(f"Debug loop failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def merge_mr_step(self, project_info: Dict[str, Any], mr: Any) -> Dict[str, Any]:
        """Execute MR merge step"""
        try:
            from controller.main_workflow.step_merge_mr import merge_mr_and_wait_pipeline
            merge_mr_and_wait_pipeline(self.config, project_info, mr)

            return {
                "status": "completed",
                "project_info": project_info,
                "merge_request": mr
            }

        except Exception as e:
            logger.error(f"MR merge failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def post_merge_monitor_step(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute post-merge monitoring step"""
        try:
            from controller.main_workflow.step_post_merge_monitor import monitor_post_merge_pipeline
            monitor_post_merge_pipeline(self.config, project_info)

            # Extract deployment URL
            deployment_url = self._extract_deployment_url(project_info)

            return {
                "status": "completed",
                "project_info": project_info,
                "deployment_url": deployment_url
            }

        except Exception as e:
            logger.error(f"Post-merge monitoring failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _extract_deployment_url(self, project_info: Dict[str, Any]) -> Optional[str]:
        """Extract deployment URL from project info"""
        project_name = project_info.get("project_name", "unknown")
        # This would be replaced with actual deployment URL extraction logic
        return f"https://deploy.example.com/{project_name.replace('/', '-')}"
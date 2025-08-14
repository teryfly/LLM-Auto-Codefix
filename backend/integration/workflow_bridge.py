import asyncio
import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from config.config_models import AppConfig
from models.web.api_models import WorkflowStartRequest
from models.web.workflow_models import WorkflowState
from integration.legacy_adapter import LegacyControllerAdapter
logger = logging.getLogger("workflow_bridge")
class WorkflowBridge:
    """Bridge between web API and existing workflow controllers"""
    def __init__(self, config: AppConfig):
        self.config = config
        self.legacy_adapter = LegacyControllerAdapter(config)
    async def execute_step(self, step_name: str, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Optional[Any]:
        """Execute a workflow step using legacy controllers"""
        try:
            logger.info(f"Executing step: {step_name}")
            if step_name == "prepare_project":
                return await self._execute_prepare_project(workflow_state, request)
            elif step_name == "create_mr":
                return await self._execute_create_mr(workflow_state, request)
            elif step_name == "debug_loop":
                return await self._execute_debug_loop(workflow_state, request)
            elif step_name == "merge_mr":
                return await self._execute_merge_mr(workflow_state, request)
            elif step_name == "post_merge_monitor":
                return await self._execute_post_merge_monitor(workflow_state, request)
            else:
                raise ValueError(f"Unknown step: {step_name}")
        except Exception as e:
            logger.error(f"Step execution failed: {step_name} - {e}")
            raise
    async def _execute_prepare_project(self, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Dict[str, Any]:
        """Execute project preparation step"""
        loop = asyncio.get_event_loop()
        # 传递项目名称到 prepare_project_step
        result = await loop.run_in_executor(
            None, 
            self.legacy_adapter.prepare_project_step,
            request.project_name  # 传递项目名称
        )
        if result["status"] == "completed":
            workflow_state.project_info = result["project_info"]
            return result
        else:
            raise Exception(result.get("error", "Project preparation failed"))
    async def _execute_create_mr(self, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Dict[str, Any]:
        """Execute merge request creation step"""
        if not workflow_state.project_info:
            raise ValueError("Project info not available")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.legacy_adapter.create_mr_step,
            workflow_state.project_info
        )
        if result["status"] == "completed":
            # Store MR info in workflow state
            workflow_state.pipeline_info = {
                "merge_request": result["merge_request"],
                "pipeline_id": workflow_state.project_info.get("pipeline_id")
            }
            return result
        else:
            raise Exception(result.get("error", "MR creation failed"))
    async def _execute_debug_loop(self, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Dict[str, Any]:
        """Execute debug loop step"""
        if not workflow_state.project_info or not workflow_state.pipeline_info:
            raise ValueError("Project info or pipeline info not available")
        mr = workflow_state.pipeline_info.get("merge_request")
        if not mr:
            raise ValueError("Merge request not available")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.legacy_adapter.debug_loop_step,
            workflow_state.project_info,
            mr
        )
        if result["status"] == "completed":
            return result
        else:
            raise Exception(result.get("error", "Debug loop failed"))
    async def _execute_merge_mr(self, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Dict[str, Any]:
        """Execute MR merge step"""
        if not workflow_state.project_info or not workflow_state.pipeline_info:
            raise ValueError("Project info or pipeline info not available")
        mr = workflow_state.pipeline_info.get("merge_request")
        if not mr:
            raise ValueError("Merge request not available")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.legacy_adapter.merge_mr_step,
            workflow_state.project_info,
            mr
        )
        if result["status"] == "completed":
            # Update pipeline info with merged pipeline
            workflow_state.pipeline_info["merged_pipeline_id"] = workflow_state.project_info.get("merged_pipeline_id")
            return result
        else:
            raise Exception(result.get("error", "MR merge failed"))
    async def _execute_post_merge_monitor(self, workflow_state: WorkflowState, request: WorkflowStartRequest) -> Dict[str, Any]:
        """Execute post-merge monitoring step"""
        if not workflow_state.project_info:
            raise ValueError("Project info not available")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.legacy_adapter.post_merge_monitor_step,
            workflow_state.project_info
        )
        if result["status"] == "completed":
            # Store deployment info
            workflow_state.pipeline_info = workflow_state.pipeline_info or {}
            workflow_state.pipeline_info["deployment_url"] = result.get("deployment_url")
            return result
        else:
            raise Exception(result.get("error", "Post-merge monitoring failed"))
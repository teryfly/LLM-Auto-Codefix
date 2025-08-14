import asyncio
import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from models.web.api_models import WorkflowStartRequest, WorkflowStatusResponse
from models.web.workflow_models import WorkflowState, WorkflowStep
from services.web.session_service import SessionService
from services.background.workflow_executor import WorkflowExecutor

logger = logging.getLogger("workflow_service")

class WorkflowService:
    def __init__(self, config: AppConfig, session_service: SessionService):
        self.config = config
        self.session_service = session_service
        self.active_workflows: Dict[str, WorkflowExecutor] = {}

    def start_workflow(self, session_id: str, request: WorkflowStartRequest) -> None:
        """Start a new workflow execution"""
        if session_id in self.active_workflows:
            raise ValueError(f"Workflow already running for session {session_id}")

        # Create workflow executor
        executor = WorkflowExecutor(self.config, session_id, request)
        self.active_workflows[session_id] = executor

        # Start workflow in background
        asyncio.create_task(self._run_workflow(session_id, executor))

        logger.info(f"Workflow started for session {session_id}")

    async def _run_workflow(self, session_id: str, executor: WorkflowExecutor):
        """Run workflow in background"""
        try:
            await executor.execute()
        except Exception as e:
            logger.error(f"Workflow execution failed for session {session_id}: {e}")
        finally:
            # Clean up completed workflow
            if session_id in self.active_workflows:
                del self.active_workflows[session_id]

    def get_workflow_status(self, session_id: str) -> WorkflowStatusResponse:
        """Get current workflow status"""
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        executor = self.active_workflows.get(session_id)
        if executor:
            # Workflow is running
            current_state = executor.get_current_state()
            return WorkflowStatusResponse(
                session_id=session_id,
                status=current_state.status,
                current_step=current_state.current_step,
                steps=current_state.steps,
                project_info=current_state.project_info,
                pipeline_info=current_state.pipeline_info,
                error_message=current_state.error_message,
                started_at=current_state.started_at,
                updated_at=datetime.utcnow()
            )
        else:
            # Workflow completed or not started
            workflow_state = session.workflow_state
            if workflow_state:
                return WorkflowStatusResponse(
                    session_id=session_id,
                    status=workflow_state.status,
                    current_step=workflow_state.current_step,
                    steps=workflow_state.steps,
                    project_info=workflow_state.project_info,
                    pipeline_info=workflow_state.pipeline_info,
                    error_message=workflow_state.error_message,
                    started_at=workflow_state.started_at,
                    updated_at=workflow_state.updated_at
                )
            else:
                raise ValueError(f"No workflow state found for session {session_id}")

    def stop_workflow(self, session_id: str, force: bool = False) -> None:
        """Stop a running workflow"""
        executor = self.active_workflows.get(session_id)
        if executor:
            executor.stop(force)
            logger.info(f"Workflow stop requested for session {session_id}")
        else:
            raise ValueError(f"No active workflow found for session {session_id}")

    def get_workflow_logs(self, session_id: str, offset: int = 0, limit: int = 100) -> list:
        """Get workflow execution logs"""
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get logs from session or executor
        executor = self.active_workflows.get(session_id)
        if executor:
            return executor.get_logs(offset, limit)
        else:
            # Return stored logs from session
            return session.logs[offset:offset+limit] if session.logs else []

    def cleanup_completed_workflows(self) -> None:
        """Clean up completed workflow executors"""
        completed = []
        for session_id, executor in self.active_workflows.items():
            if executor.is_completed():
                completed.append(session_id)

        for session_id in completed:
            del self.active_workflows[session_id]
            logger.info(f"Cleaned up completed workflow for session {session_id}")
import logging
from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.workflow_models import WorkflowState

logger = logging.getLogger("workflow_state")

class WorkflowStateManager:
    """In-memory workflow state management"""

    def __init__(self):
        self.workflow_states: Dict[str, WorkflowState] = {}

    def create_workflow_state(self, workflow_state: WorkflowState) -> None:
        """Create a new workflow state"""
        self.workflow_states[workflow_state.session_id] = workflow_state
        logger.debug(f"Created workflow state for session {workflow_state.session_id}")

    def get_workflow_state(self, session_id: str) -> Optional[WorkflowState]:
        """Get workflow state by session ID"""
        return self.workflow_states.get(session_id)

    def update_workflow_state(self, session_id: str, **updates) -> None:
        """Update workflow state"""
        workflow_state = self.workflow_states.get(session_id)
        if not workflow_state:
            raise ValueError(f"Workflow state for session {session_id} not found")

        for key, value in updates.items():
            if hasattr(workflow_state, key):
                setattr(workflow_state, key, value)

        workflow_state.updated_at = datetime.utcnow()
        logger.debug(f"Updated workflow state for session {session_id}")

    def delete_workflow_state(self, session_id: str) -> None:
        """Delete workflow state"""
        if session_id in self.workflow_states:
            del self.workflow_states[session_id]
            logger.debug(f"Deleted workflow state for session {session_id}")

    def list_workflow_states(self) -> Dict[str, WorkflowState]:
        """List all workflow states"""
        return self.workflow_states.copy()

    def get_active_workflows(self) -> Dict[str, WorkflowState]:
        """Get all active (running) workflow states"""
        active = {}
        for session_id, state in self.workflow_states.items():
            if state.status in ["running", "initializing"]:
                active[session_id] = state
        return active

    def clear_completed_workflows(self, keep_recent_hours: int = 24) -> int:
        """Clear completed workflow states older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=keep_recent_hours)
        to_remove = []

        for session_id, state in self.workflow_states.items():
            if (state.status in ["completed", "failed", "cancelled"] and
                state.completed_at and state.completed_at < cutoff_time):
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.workflow_states[session_id]

        logger.debug(f"Cleared {len(to_remove)} completed workflows")
        return len(to_remove)
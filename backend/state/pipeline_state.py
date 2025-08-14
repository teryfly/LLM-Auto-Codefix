import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

logger = logging.getLogger("pipeline_state")

class PipelineState:
    def __init__(self, session_id: str, project_id: int, pipeline_id: int, **kwargs):
        self.session_id = session_id
        self.project_id = project_id
        self.pipeline_id = pipeline_id
        self.status = kwargs.get('status', 'unknown')
        self.ref = kwargs.get('ref')
        self.sha = kwargs.get('sha')
        self.web_url = kwargs.get('web_url')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())

class PipelineStateManager:
    """In-memory pipeline state management"""

    def __init__(self):
        self.pipeline_states: Dict[str, PipelineState] = {}

    def create_state(self, session_id: str, project_id: int, pipeline_id: int, **kwargs) -> None:
        """Create a new pipeline state"""
        pipeline_state = PipelineState(session_id, project_id, pipeline_id, **kwargs)
        self.pipeline_states[session_id] = pipeline_state
        logger.debug(f"Created pipeline state for session {session_id}")

    def get_state(self, session_id: str) -> Optional[PipelineState]:
        """Get pipeline state by session ID"""
        return self.pipeline_states.get(session_id)

    def update_state(self, session_id: str, project_id: int = None, pipeline_id: int = None, **kwargs) -> None:
        """Update pipeline state"""
        pipeline_state = self.pipeline_states.get(session_id)
        if not pipeline_state:
            # Create new state if it doesn't exist
            if project_id is not None and pipeline_id is not None:
                self.create_state(session_id, project_id, pipeline_id, **kwargs)
                return
            else:
                raise ValueError(f"Pipeline state for session {session_id} not found")

        # Update existing state
        if project_id is not None:
            pipeline_state.project_id = project_id
        if pipeline_id is not None:
            pipeline_state.pipeline_id = pipeline_id

        for key, value in kwargs.items():
            if hasattr(pipeline_state, key):
                setattr(pipeline_state, key, value)

        pipeline_state.updated_at = datetime.utcnow()
        logger.debug(f"Updated pipeline state for session {session_id}")

    def delete_state(self, session_id: str) -> None:
        """Delete pipeline state"""
        if session_id in self.pipeline_states:
            del self.pipeline_states[session_id]
            logger.debug(f"Deleted pipeline state for session {session_id}")

    def list_states(self) -> Dict[str, PipelineState]:
        """List all pipeline states"""
        return self.pipeline_states.copy()

    def clear_old_states(self, keep_recent_hours: int = 24) -> int:
        """Clear old pipeline states"""
        cutoff_time = datetime.utcnow() - timedelta(hours=keep_recent_hours)
        to_remove = []

        for session_id, state in self.pipeline_states.items():
            if state.updated_at < cutoff_time:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.pipeline_states[session_id]
            logger.debug(f"Removed old pipeline state for session {session_id}")

        return len(to_remove)
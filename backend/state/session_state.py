import logging
from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from models.web.session_models import Session

logger = logging.getLogger("session_state")

class SessionStateManager:
    """In-memory session state management"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self, session: Session) -> None:
        """Create a new session"""
        self.sessions[session.id] = session
        logger.debug(f"Created session {session.id}")

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, **updates) -> None:
        """Update session data"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.utcnow()
        logger.debug(f"Updated session {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug(f"Deleted session {session_id}")

    def list_sessions(self) -> Dict[str, Session]:
        """List all sessions"""
        return self.sessions.copy()

    def clear_all_sessions(self) -> None:
        """Clear all sessions (for testing/cleanup)"""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared {count} sessions")
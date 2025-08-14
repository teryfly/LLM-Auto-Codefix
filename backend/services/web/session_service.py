import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from models.web.session_models import Session, SessionStatus
from state.session_state import SessionStateManager

logger = logging.getLogger("session_service")

class SessionService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session_manager = SessionStateManager()
        self.session_timeout = timedelta(minutes=getattr(config, 'session_timeout_minutes', 120))

    def create_session(self) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            status=SessionStatus.CREATED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.session_timeout
        )

        self.session_manager.create_session(session)
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.session_manager.get_session(session_id)
        if session and self._is_session_expired(session):
            self._expire_session(session_id)
            return None
        return session

    def update_session(self, session_id: str, **updates) -> None:
        """Update session data"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        updates['updated_at'] = datetime.utcnow()
        self.session_manager.update_session(session_id, **updates)
        logger.debug(f"Updated session {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Delete a session"""
        self.session_manager.delete_session(session_id)
        logger.info(f"Deleted session: {session_id}")

    def list_active_sessions(self) -> Dict[str, Session]:
        """List all active sessions"""
        all_sessions = self.session_manager.list_sessions()
        active_sessions = {}

        for session_id, session in all_sessions.items():
            if not self._is_session_expired(session):
                active_sessions[session_id] = session
            else:
                # Clean up expired session
                self._expire_session(session_id)

        return active_sessions

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        all_sessions = self.session_manager.list_sessions()
        expired_count = 0

        for session_id, session in all_sessions.items():
            if self._is_session_expired(session):
                self._expire_session(session_id)
                expired_count += 1

        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")

        return expired_count

    def extend_session(self, session_id: str, minutes: int = None) -> None:
        """Extend session expiration time"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        extension = timedelta(minutes=minutes or 120)
        new_expires_at = datetime.utcnow() + extension

        self.update_session(session_id, expires_at=new_expires_at)
        logger.info(f"Extended session {session_id} until {new_expires_at}")

    def _is_session_expired(self, session: Session) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > session.expires_at

    def _expire_session(self, session_id: str) -> None:
        """Mark session as expired and clean up"""
        try:
            self.update_session(session_id, status=SessionStatus.EXPIRED)
            # Could add cleanup logic here
            logger.info(f"Session {session_id} expired")
        except:
            # Session might already be deleted
            pass
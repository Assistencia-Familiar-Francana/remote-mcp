"""Session management following SOLID principles."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .session import SSHSession, SessionInfo
from .config import get_config

logger = logging.getLogger(__name__)

@dataclass
class SessionStats:
    """Statistics about session management."""
    total_sessions: int
    active_sessions: int
    expired_sessions: int
    max_sessions: int

class SessionManager:
    """Manages SSH sessions following Single Responsibility Principle."""
    
    def __init__(self):
        self.config = get_config()
        self.sessions: Dict[str, SSHSession] = {}
        self.session_creation_times: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def create_session(self, session_id: str, host: str, port: int, username: str) -> SSHSession:
        """Create a new SSH session."""
        if session_id in self.sessions:
            raise ValueError(f"Session '{session_id}' already exists")
        
        if len(self.sessions) >= self.config.security.max_sessions:
            # Remove oldest session
            await self._remove_oldest_session()
        
        session = SSHSession(session_id, host, port, username)
        self.sessions[session_id] = session
        self.session_creation_times[session_id] = datetime.now()
        
        logger.info(f"Created session {session_id} for {username}@{host}:{port}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SSHSession]:
        """Get an existing session by ID."""
        return self.sessions.get(session_id)
    
    async def remove_session(self, session_id: str) -> bool:
        """Remove a session by ID."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        if session.connected:
            await session.disconnect()
        
        del self.sessions[session_id]
        if session_id in self.session_creation_times:
            del self.session_creation_times[session_id]
        
        logger.info(f"Removed session {session_id}")
        return True
    
    def list_sessions(self) -> List[SessionInfo]:
        """List all active sessions."""
        session_infos = []
        for session_id, session in self.sessions.items():
            session_infos.append(session.get_session_info())
        return session_infos
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        if not self.sessions:
            return 0
        
        expired_count = 0
        current_time = datetime.now()
        max_age = timedelta(hours=self.config.security.session_timeout_hours)
        
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            creation_time = self.session_creation_times.get(session_id)
            if not creation_time:
                continue
            
            age = current_time - creation_time
            if age > max_age:
                sessions_to_remove.append(session_id)
                expired_count += 1
        
        # Remove expired sessions
        for session_id in sessions_to_remove:
            await self.remove_session(session_id)
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired sessions")
        
        return expired_count
    
    async def _remove_oldest_session(self) -> None:
        """Remove the oldest session when at capacity."""
        if not self.sessions:
            return
        
        oldest_session_id = min(
            self.session_creation_times.keys(),
            key=lambda sid: self.session_creation_times[sid]
        )
        
        logger.warning(f"Session limit reached, removing oldest session: {oldest_session_id}")
        await self.remove_session(oldest_session_id)
    
    def get_session_stats(self) -> SessionStats:
        """Get statistics about session management."""
        current_time = datetime.now()
        max_age = timedelta(hours=self.config.security.session_timeout_hours)
        
        expired_count = 0
        for creation_time in self.session_creation_times.values():
            if current_time - creation_time > max_age:
                expired_count += 1
        
        return SessionStats(
            total_sessions=len(self.sessions),
            active_sessions=len(self.sessions) - expired_count,
            expired_sessions=expired_count,
            max_sessions=self.config.security.max_sessions
        )
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid and not expired."""
        if session_id not in self.sessions:
            return False
        
        creation_time = self.session_creation_times.get(session_id)
        if not creation_time:
            return False
        
        current_time = datetime.now()
        max_age = timedelta(hours=self.config.security.session_timeout_hours)
        
        return current_time - creation_time <= max_age
    
    async def disconnect_all_sessions(self) -> int:
        """Disconnect all active sessions."""
        disconnected_count = 0
        
        for session_id, session in list(self.sessions.items()):
            if session.connected:
                await session.disconnect()
                disconnected_count += 1
        
        logger.info(f"Disconnected {disconnected_count} sessions")
        return disconnected_count
    
    def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started session cleanup task")
    
    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.info("Stopped session cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleaning up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

# Global session manager instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

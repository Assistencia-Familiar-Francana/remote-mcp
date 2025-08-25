"""Interactive password service for MCP SSH operations."""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PasswordRequest:
    """Represents a password request."""
    request_id: str
    prompt_text: str
    prompt_type: str
    session_id: str
    host: str
    username: str
    command: str
    timestamp: datetime
    timeout_seconds: int = 60

@dataclass
class PasswordResponse:
    """Represents a password response."""
    request_id: str
    password: Optional[str] = None
    cancelled: bool = False
    timeout: bool = False
    error: Optional[str] = None

class InteractivePasswordService:
    """Service for handling interactive password requests."""
    
    def __init__(self):
        self.pending_requests: Dict[str, PasswordRequest] = {}
        self.response_callbacks: Dict[str, asyncio.Future] = {}
        self.password_callback: Optional[Callable[[PasswordRequest], Awaitable[Optional[str]]]] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def set_password_callback(self, callback: Callable[[PasswordRequest], Awaitable[Optional[str]]]) -> None:
        """Set the callback function for requesting passwords from the user."""
        self.password_callback = callback
        logger.info("Password callback set for interactive password service")
    
    async def request_password(
        self,
        prompt_text: str,
        prompt_type: str,
        session_id: str,
        host: str,
        username: str,
        command: str,
        timeout_seconds: int = 60
    ) -> Optional[str]:
        """Request a password from the user."""
        import uuid
        
        request_id = str(uuid.uuid4())
        request = PasswordRequest(
            request_id=request_id,
            prompt_text=prompt_text,
            prompt_type=prompt_type,
            session_id=session_id,
            host=host,
            username=username,
            command=command,
            timestamp=datetime.now(),
            timeout_seconds=timeout_seconds
        )
        
        # Store the request
        self.pending_requests[request_id] = request
        
        # Create a future for the response
        future = asyncio.Future()
        self.response_callbacks[request_id] = future
        
        try:
            # Use the callback to request password from user
            if self.password_callback:
                password = await self.password_callback(request)
                if password:
                    future.set_result(password)
                else:
                    future.set_result(None)  # Cancelled
            else:
                # Fallback: wait for manual response
                logger.warning(f"No password callback set, waiting for manual response for request {request_id}")
                password = await asyncio.wait_for(future, timeout=timeout_seconds)
            
            return password
            
        except asyncio.TimeoutError:
            logger.warning(f"Password request {request_id} timed out")
            future.set_result(None)
            return None
        except Exception as e:
            logger.error(f"Error in password request {request_id}: {e}")
            future.set_result(None)
            return None
        finally:
            # Clean up
            self.pending_requests.pop(request_id, None)
            self.response_callbacks.pop(request_id, None)
    
    def provide_password(self, request_id: str, password: str) -> bool:
        """Provide a password for a pending request."""
        if request_id not in self.response_callbacks:
            logger.warning(f"Password response for unknown request: {request_id}")
            return False
        
        future = self.response_callbacks[request_id]
        if not future.done():
            future.set_result(password)
            logger.info(f"Password provided for request {request_id}")
            return True
        else:
            logger.warning(f"Password response for completed request: {request_id}")
            return False
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending password request."""
        if request_id not in self.response_callbacks:
            return False
        
        future = self.response_callbacks[request_id]
        if not future.done():
            future.set_result(None)  # Cancelled
            logger.info(f"Password request {request_id} cancelled")
            return True
        return False
    
    def get_pending_requests(self) -> Dict[str, PasswordRequest]:
        """Get all pending password requests."""
        return self.pending_requests.copy()
    
    def cleanup_expired_requests(self) -> int:
        """Clean up expired password requests."""
        now = datetime.now()
        expired_requests = []
        
        for request_id, request in self.pending_requests.items():
            if now - request.timestamp > timedelta(seconds=request.timeout_seconds):
                expired_requests.append(request_id)
        
        for request_id in expired_requests:
            self.cancel_request(request_id)
            self.pending_requests.pop(request_id, None)
        
        if expired_requests:
            logger.info(f"Cleaned up {len(expired_requests)} expired password requests")
        
        return len(expired_requests)
    
    def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started password service cleanup task")
    
    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.info("Stopped password service cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleaning up expired requests."""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                self.cleanup_expired_requests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Password service cleanup error: {e}")
                await asyncio.sleep(10)  # Retry after 10 seconds

# Global password service instance
_password_service: Optional[InteractivePasswordService] = None

def get_password_service() -> InteractivePasswordService:
    """Get the global password service instance."""
    global _password_service
    if _password_service is None:
        _password_service = InteractivePasswordService()
    return _password_service

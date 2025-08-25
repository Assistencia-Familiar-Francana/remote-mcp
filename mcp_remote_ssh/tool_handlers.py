"""Tool handlers for MCP SSH operations following SOLID principles."""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .config import get_config
from .session_manager import get_session_manager
from .session import SessionInfo
from .security import get_security_manager
from .interactive_password_service import get_password_service, PasswordRequest

logger = logging.getLogger(__name__)

@dataclass
class ToolContext:
    """Context for tool execution."""
    config: Any
    session_manager: Any
    security_manager: Any

class ToolHandler(ABC):
    """Abstract base class for tool handlers following Interface Segregation Principle."""
    
    def __init__(self, context: ToolContext):
        self.context = context
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool operation."""
        pass
    
    @abstractmethod
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate tool parameters. Returns error message if invalid."""
        pass

class SSHConnectHandler(ToolHandler):
    """Handles SSH connection establishment."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Establish SSH connection to a remote host."""
        try:
            # Validate parameters
            error = self.validate_parameters(**kwargs)
            if error:
                return {"success": False, "error": error}
            
            # Extract parameters
            host = kwargs.get('host') or self.context.config.ssh.default_host
            port = kwargs.get('port') or self.context.config.ssh.default_port
            username = kwargs.get('username') or self.context.config.ssh.default_username
            session_id = kwargs.get('session_id') or str(uuid.uuid4())[:8]
            auth = kwargs.get('auth')
            
            # Create session
            session = await self.context.session_manager.create_session(
                session_id=session_id,
                host=host,
                port=port,
                username=username
            )
            
            # Handle authentication
            auth_result = await self._handle_authentication(session, auth)
            if not auth_result["success"]:
                return auth_result
            
            return {
                "success": True,
                "session_id": session_id,
                "host": host,
                "username": session.username,
                "message": f"Connected to {session.username}@{host}:{port}"
            }
            
        except Exception as e:
            logger.error(f"SSH connect error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH connection parameters."""
        host = kwargs.get('host') or self.context.config.ssh.default_host
        username = kwargs.get('username') or self.context.config.ssh.default_username
        
        if not host:
            return "Host is required. Either provide it as parameter or set MCP_SSH_HOST environment variable."
        if not username:
            return "Username is required. Either provide it as parameter or set MCP_SSH_USER environment variable."
        
        return None
    
    async def _handle_authentication(self, session, auth: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle authentication for the session."""
        auth_method = "key"
        auth_kwargs = {}
        
        if auth:
            if "password" in auth:
                auth_method = "password"
                auth_kwargs["password"] = auth["password"]
            elif "key_path" in auth:
                auth_kwargs["key_path"] = auth["key_path"]
            elif "key_pem_base64" in auth:
                auth_kwargs["key_pem_base64"] = auth["key_pem_base64"]
        else:
            # Use default key path from config
            if self.context.config.ssh.key_path:
                auth_kwargs["key_path"] = self.context.config.ssh.key_path
        
        success = await session.connect(auth_method, **auth_kwargs)
        
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to establish SSH connection"}

class SSHRunHandler(ToolHandler):
    """Handles SSH command execution."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a command in an existing SSH session."""
        try:
            # Validate parameters
            error = self.validate_parameters(**kwargs)
            if error:
                return {"success": False, "error": error}
            
            # Extract parameters
            session_id = kwargs['session_id']
            cmd = kwargs['cmd']
            input_data = kwargs.get('input_data')
            timeout_ms = kwargs.get('timeout_ms')
            max_bytes = kwargs.get('max_bytes')
            sudo_password = kwargs.get('sudo_password')
            
            # Get session
            session = self.context.session_manager.get_session(session_id)
            if not session:
                return {"success": False, "error": f"Session '{session_id}' not found"}
            
            if not session.connected:
                return {"success": False, "error": f"Session '{session_id}' not connected"}
            
            # Get sudo password from config if not provided
            if not sudo_password and self.context.config.ssh.sudo_password:
                sudo_password = self.context.config.ssh.sudo_password
            
            # Execute command
            result = await session.execute_command(
                command=cmd,
                input_data=input_data,
                timeout_ms=timeout_ms,
                max_bytes=max_bytes,
                sudo_password=sudo_password
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_status": result.exit_status,
                "duration_ms": result.duration_ms,
                "truncated": result.truncated
            }
            
        except Exception as e:
            logger.error(f"SSH run error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH run parameters."""
        if 'session_id' not in kwargs:
            return "session_id is required"
        if 'cmd' not in kwargs:
            return "cmd is required"
        return None

class SSHDisconnectHandler(ToolHandler):
    """Handles SSH session disconnection."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Disconnect SSH session."""
        try:
            # Validate parameters
            error = self.validate_parameters(**kwargs)
            if error:
                return {"success": False, "error": error}
            
            session_id = kwargs['session_id']
            await self.context.session_manager.remove_session(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Session '{session_id}' disconnected"
            }
            
        except Exception as e:
            logger.error(f"SSH disconnect error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH disconnect parameters."""
        if 'session_id' not in kwargs:
            return "session_id is required"
        return None

class SSHListSessionsHandler(ToolHandler):
    """Handles listing SSH sessions."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """List all active SSH sessions."""
        try:
            sessions = self.context.session_manager.list_sessions()
            
            session_list = []
            for session_info in sessions:
                session_list.append({
                    "session_id": session_info.session_id,
                    "host": session_info.host,
                    "username": session_info.username,
                    "connected_at": session_info.connected_at.isoformat(),
                    "last_used": session_info.last_used.isoformat(),
                    "current_dir": session_info.current_dir
                })
            
            return {
                "success": True,
                "sessions": session_list,
                "count": len(session_list)
            }
            
        except Exception as e:
            logger.error(f"SSH list sessions error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH list sessions parameters."""
        # No parameters required for listing sessions
        return None

class SSHListPasswordRequestsHandler(ToolHandler):
    """Handles listing pending password requests."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """List all pending password requests."""
        try:
            password_service = get_password_service()
            pending_requests = password_service.get_pending_requests()
            
            request_list = []
            for request_id, request in pending_requests.items():
                request_list.append({
                    "request_id": request_id,
                    "prompt_text": request.prompt_text,
                    "prompt_type": request.prompt_type,
                    "session_id": request.session_id,
                    "host": request.host,
                    "username": request.username,
                    "command": request.command,
                    "timestamp": request.timestamp.isoformat(),
                    "timeout_seconds": request.timeout_seconds
                })
            
            return {
                "success": True,
                "requests": request_list,
                "count": len(request_list)
            }
            
        except Exception as e:
            logger.error(f"SSH list password requests error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH list password requests parameters."""
        # No parameters required for listing requests
        return None

class SSHProvidePasswordHandler(ToolHandler):
    """Handles providing passwords for pending requests."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Provide a password for a pending request."""
        try:
            # Validate parameters
            error = self.validate_parameters(**kwargs)
            if error:
                return {"success": False, "error": error}
            
            request_id = kwargs['request_id']
            password = kwargs['password']
            
            password_service = get_password_service()
            success = password_service.provide_password(request_id, password)
            
            if success:
                return {
                    "success": True,
                    "request_id": request_id,
                    "message": f"Password provided for request {request_id}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to provide password for request {request_id}"
                }
            
        except Exception as e:
            logger.error(f"SSH provide password error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH provide password parameters."""
        if 'request_id' not in kwargs:
            return "request_id is required"
        if 'password' not in kwargs:
            return "password is required"
        return None

class SSHCancelPasswordRequestHandler(ToolHandler):
    """Handles cancelling pending password requests."""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Cancel a pending password request."""
        try:
            # Validate parameters
            error = self.validate_parameters(**kwargs)
            if error:
                return {"success": False, "error": error}
            
            request_id = kwargs['request_id']
            
            password_service = get_password_service()
            success = password_service.cancel_request(request_id)
            
            if success:
                return {
                    "success": True,
                    "request_id": request_id,
                    "message": f"Password request {request_id} cancelled"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to cancel request {request_id}"
                }
            
        except Exception as e:
            logger.error(f"SSH cancel password request error: {e}")
            return {"success": False, "error": str(e)}
    
    def validate_parameters(self, **kwargs) -> Optional[str]:
        """Validate SSH cancel password request parameters."""
        if 'request_id' not in kwargs:
            return "request_id is required"
        return None

class ToolHandlerFactory:
    """Factory for creating tool handlers following Factory Pattern."""
    
    def __init__(self):
        self.context = ToolContext(
            config=get_config(),
            session_manager=get_session_manager(),
            security_manager=get_security_manager()
        )
    
    def create_handler(self, tool_name: str) -> ToolHandler:
        """Create a tool handler for the specified tool."""
        handlers = {
            'ssh_connect': SSHConnectHandler,
            'ssh_run': SSHRunHandler,
            'ssh_disconnect': SSHDisconnectHandler,
            'ssh_list_sessions': SSHListSessionsHandler,
            'ssh_list_password_requests': SSHListPasswordRequestsHandler,
            'ssh_provide_password': SSHProvidePasswordHandler,
            'ssh_cancel_password_request': SSHCancelPasswordRequestHandler,
        }
        
        handler_class = handlers.get(tool_name)
        if not handler_class:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return handler_class(self.context)

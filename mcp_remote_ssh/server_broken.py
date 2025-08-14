"""MCP Remote SSH Server - Main server implementation."""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional, Union
import uuid
import base64
from datetime import datetime

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server import NotificationOptions
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        CallToolRequest, ListResourcesRequest, ListToolsRequest,
        ReadResourceRequest, GetPromptRequest, ListPromptsRequest
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP dependencies not installed. Install with: pip install modelcontextprotocol")

from .config import get_config
from .session import get_session_manager, CommandResult, SessionInfo
from .security import get_security_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
config = get_config()
session_manager = get_session_manager()
security_manager = get_security_manager()

# Create FastMCP app (only if MCP is available)
if MCP_AVAILABLE:
    mcp = FastMCP("Remote SSH Server", version="0.1.0")
else:
    mcp = None

# Define MCP tools only if MCP is available
if MCP_AVAILABLE:
    @mcp.tool()
    async def ssh_connect(
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        auth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Establish SSH connection to a remote host.
    
    Args:
        host: Remote hostname or IP address
        port: SSH port (default: 22)
        username: SSH username (optional, uses config default)
        session_id: Session identifier (optional, auto-generated)
        auth: Authentication details with keys:
            - key_path: Path to private key file
            - key_pem_base64: Base64-encoded private key
            - password: Password for authentication
    
    Returns:
        Dict with connection status and session info
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        # Create session
        session = await session_manager.create_session(
            session_id=session_id,
            host=host,
            port=port,
            username=username
        )
        
        # Determine authentication method
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
            if config.ssh.key_path:
                auth_kwargs["key_path"] = config.ssh.key_path
        
        # Connect
        success = await session.connect(auth_method, **auth_kwargs)
        
        if success:
            return {
                "success": True,
                "session_id": session_id,
                "host": host,
                "username": session.username,
                "message": f"Connected to {session.username}@{host}:{port}"
            }
        else:
            return {
                "success": False,
                "session_id": session_id,
                "error": "Failed to establish SSH connection"
            }
            
    except Exception as e:
        logger.error(f"SSH connect error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_run(
    session_id: str,
    cmd: str,
    input_data: Optional[str] = None,
    timeout_ms: Optional[int] = None,
    max_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a command in an existing SSH session.
    
    Args:
        session_id: SSH session identifier
        cmd: Command to execute
        input_data: Optional input to send to command
        timeout_ms: Command timeout in milliseconds
        max_bytes: Maximum output bytes
    
    Returns:
        Dict with command execution results
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        if not session.connected:
            return {
                "success": False,
                "error": f"Session '{session_id}' not connected"
            }
        
        # Execute command
        result = await session.execute_command(
            command=cmd,
            input_data=input_data,
            timeout_ms=timeout_ms,
            max_bytes=max_bytes
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
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_upload(
    session_id: str,
    path: str,
    bytes_base64: str,
    mode: str = "644"
) -> Dict[str, Any]:
    """
    Upload file content to remote system.
    
    Args:
        session_id: SSH session identifier
        path: Remote file path
        bytes_base64: Base64-encoded file content
        mode: File permissions (octal string)
    
    Returns:
        Dict with upload status
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        # Decode content
        try:
            content = base64.b64decode(bytes_base64)
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid base64 content: {e}"
            }
        
        # Upload file
        success = await session.upload_file(path, content, mode)
        
        return {
            "success": success,
            "session_id": session_id,
            "path": path,
            "size_bytes": len(content),
            "message": f"Uploaded {len(content)} bytes to {path}" if success else "Upload failed"
        }
        
    except Exception as e:
        logger.error(f"SSH upload error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_download(
    session_id: str,
    path: str,
    max_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Download file content from remote system.
    
    Args:
        session_id: SSH session identifier
        path: Remote file path
        max_bytes: Maximum file size to download
    
    Returns:
        Dict with file content (base64-encoded) and metadata
    """
    try:
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        # Download file
        content = await session.download_file(path, max_bytes)
        
        if content is not None:
            return {
                "success": True,
                "session_id": session_id,
                "path": path,
                "bytes_base64": base64.b64encode(content).decode('utf-8'),
                "size_bytes": len(content)
            }
        else:
            return {
                "success": False,
                "error": "Download failed"
            }
            
    except Exception as e:
        logger.error(f"SSH download error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_disconnect(session_id: str) -> Dict[str, Any]:
    """
    Disconnect SSH session.
    
    Args:
        session_id: SSH session identifier
    
    Returns:
        Dict with disconnection status
    """
    try:
        # Remove session
        await session_manager.remove_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Session '{session_id}' disconnected"
        }
        
    except Exception as e:
        logger.error(f"SSH disconnect error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_list_sessions() -> Dict[str, Any]:
    """
    List all active SSH sessions.
    
    Returns:
        Dict with list of active sessions
    """
    try:
        sessions = session_manager.list_sessions()
        
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
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def ssh_validate_command(cmd: str) -> Dict[str, Any]:
    """
    Validate if a command is allowed to run.
    
    Args:
        cmd: Command to validate
    
    Returns:
        Dict with validation result
    """
    try:
        validation = security_manager.validate_command(cmd)
        
        return {
            "allowed": validation.allowed,
            "reason": validation.reason,
            "sanitized_cmd": validation.sanitized_cmd
        }
        
    except Exception as e:
        logger.error(f"Command validation error: {e}")
        return {
            "allowed": False,
            "reason": str(e)
        }

# Resource endpoints
@mcp.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="ssh://sessions",
            name="Active SSH Sessions",
            description="List of currently active SSH sessions",
            mimeType="application/json"
        ),
        Resource(
            uri="ssh://config",
            name="SSH Configuration",
            description="Current SSH server configuration",
            mimeType="application/json"
        )
    ]

@mcp.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "ssh://sessions":
        sessions = session_manager.list_sessions()
        session_data = []
        for session_info in sessions:
            session_data.append({
                "session_id": session_info.session_id,
                "host": session_info.host,
                "username": session_info.username,
                "connected_at": session_info.connected_at.isoformat(),
                "last_used": session_info.last_used.isoformat()
            })
        return str(session_data)
    
    elif uri == "ssh://config":
        config_data = {
            "security": {
                "allowed_commands": config.security.allowed_commands[:10],  # First 10 for brevity
                "max_output_bytes": config.security.max_output_bytes,
                "command_timeout_seconds": config.security.command_timeout_seconds,
                "max_sessions": config.security.max_sessions
            },
            "ssh": {
                "default_port": config.ssh.default_port,
                "connect_timeout": config.ssh.connect_timeout
            }
        }
        return str(config_data)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

# Cleanup task
async def cleanup_task():
    """Background task to cleanup expired sessions."""
    while True:
        try:
            await session_manager.cleanup_expired_sessions()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        print("Error: MCP dependencies not available.")
        print("Install with: pip install modelcontextprotocol paramiko pyyaml python-dotenv")
        sys.exit(1)
    
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    
    logger.info("Starting MCP Remote SSH Server")
    logger.info(f"Max sessions: {config.security.max_sessions}")
    logger.info(f"Allowed commands: {len(config.security.allowed_commands)}")
    
    # Start cleanup task
    asyncio.create_task(cleanup_task())
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()

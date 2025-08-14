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

def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        print("Error: MCP dependencies not available.")
        print("Install with: pip install modelcontextprotocol paramiko pyyaml python-dotenv")
        sys.exit(1)
    
    # Create FastMCP app
    mcp = FastMCP("Remote SSH Server", version="0.1.0")
    
    @mcp.tool()
    async def ssh_connect(
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        auth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Establish SSH connection to a remote host."""
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
        """Execute a command in an existing SSH session."""
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
    async def ssh_disconnect(session_id: str) -> Dict[str, Any]:
        """Disconnect SSH session."""
        try:
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
        """List all active SSH sessions."""
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

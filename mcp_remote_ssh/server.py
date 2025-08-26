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
from .session_manager import get_session_manager
from .session import CommandResult, SessionInfo
from .security import get_security_manager
from .tool_handlers import ToolHandlerFactory

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
tool_handler_factory = ToolHandlerFactory()

def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        print("Error: MCP dependencies not available.")
        print("Install with: pip install modelcontextprotocol paramiko pyyaml python-dotenv")
        sys.exit(1)
    
    # Create FastMCP app
    mcp = FastMCP("Remote SSH Server")
    
    @mcp.tool()
    async def ssh_connect(
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        auth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Establish SSH connection to a remote host."""
        handler = tool_handler_factory.create_handler('ssh_connect')
        return await handler.execute(
            host=host,
            port=port,
            username=username,
            session_id=session_id,
            auth=auth
        )

    @mcp.tool()
    async def ssh_run(
        session_id: str,
        cmd: str,
        input_data: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        max_bytes: Optional[int] = None,
        sudo_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in an existing SSH session."""
        handler = tool_handler_factory.create_handler('ssh_run')
        return await handler.execute(
            session_id=session_id,
            cmd=cmd,
            input_data=input_data,
            timeout_ms=timeout_ms,
            max_bytes=max_bytes,
            sudo_password=sudo_password
        )

    @mcp.tool()
    async def ssh_disconnect(session_id: str) -> Dict[str, Any]:
        """Disconnect SSH session."""
        handler = tool_handler_factory.create_handler('ssh_disconnect')
        return await handler.execute(session_id=session_id)

    @mcp.tool()
    async def ssh_list_sessions() -> Dict[str, Any]:
        """List all active SSH sessions."""
        handler = tool_handler_factory.create_handler('ssh_list_sessions')
        return await handler.execute()

    @mcp.tool()
    async def ssh_list_password_requests() -> Dict[str, Any]:
        """List all pending password requests."""
        handler = tool_handler_factory.create_handler('ssh_list_password_requests')
        return await handler.execute()

    @mcp.tool()
    async def ssh_provide_password(request_id: str, password: str) -> Dict[str, Any]:
        """Provide a password for a pending request."""
        handler = tool_handler_factory.create_handler('ssh_provide_password')
        return await handler.execute(request_id=request_id, password=password)

    @mcp.tool()
    async def ssh_cancel_password_request(request_id: str) -> Dict[str, Any]:
        """Cancel a pending password request."""
        handler = tool_handler_factory.create_handler('ssh_cancel_password_request')
        return await handler.execute(request_id=request_id)

    @mcp.tool()
    async def ssh_get_permissibility_info() -> Dict[str, Any]:
        """Get information about current permissibility level and restrictions."""
        handler = tool_handler_factory.create_handler('ssh_get_permissibility_info')
        return await handler.execute()

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
    logger.info(f"Permissibility level: {config.security.permissibility_level.value}")
    logger.info(f"Allowed commands: {len(config.security.get_allowed_commands())}")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()

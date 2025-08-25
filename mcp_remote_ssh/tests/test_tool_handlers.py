"""Tests for tool handlers following TDD principles."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ..tool_handlers import (
    ToolHandler, SSHConnectHandler, SSHRunHandler, SSHDisconnectHandler,
    SSHListSessionsHandler, ToolHandlerFactory, ToolContext
)
from ..session import SessionInfo
from datetime import datetime

class TestToolHandler:
    """Test the abstract ToolHandler base class."""
    
    def test_tool_handler_is_abstract(self):
        """Test that ToolHandler cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ToolHandler(Mock())

class TestSSHConnectHandler:
    """Test SSH connection handler."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock tool context."""
        context = Mock(spec=ToolContext)
        context.config.ssh.default_host = "default.host.com"
        context.config.ssh.default_port = 22
        context.config.ssh.default_username = "default_user"
        context.config.ssh.key_path = "/path/to/key"
        return context
    
    @pytest.fixture
    def handler(self, mock_context):
        """Create an SSH connect handler."""
        return SSHConnectHandler(mock_context)
    
    def test_validate_parameters_with_valid_params(self, handler):
        """Test parameter validation with valid parameters."""
        error = handler.validate_parameters(host="test.host.com", username="test_user")
        assert error is None
    
    def test_validate_parameters_without_host(self, handler):
        """Test parameter validation without host."""
        error = handler.validate_parameters(username="test_user")
        assert "Host is required" in error
    
    def test_validate_parameters_without_username(self, handler):
        """Test parameter validation without username."""
        error = handler.validate_parameters(host="test.host.com")
        assert "Username is required" in error
    
    @pytest.mark.asyncio
    async def test_execute_successful_connection(self, handler, mock_context):
        """Test successful SSH connection."""
        # Mock session creation and connection
        mock_session = AsyncMock()
        mock_session.username = "test_user"
        mock_context.session_manager.create_session.return_value = mock_session
        
        result = await handler.execute(
            host="test.host.com",
            port=2222,
            username="test_user",
            session_id="test_session"
        )
        
        assert result["success"] is True
        assert result["session_id"] == "test_session"
        assert result["host"] == "test.host.com"
        assert result["username"] == "test_user"
    
    @pytest.mark.asyncio
    async def test_execute_connection_failure(self, handler, mock_context):
        """Test SSH connection failure."""
        # Mock session creation but connection failure
        mock_session = AsyncMock()
        mock_session.connect.return_value = False
        mock_context.session_manager.create_session.return_value = mock_session
        
        result = await handler.execute(
            host="test.host.com",
            username="test_user"
        )
        
        assert result["success"] is False
        assert "Failed to establish SSH connection" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_with_password_auth(self, handler, mock_context):
        """Test SSH connection with password authentication."""
        mock_session = AsyncMock()
        mock_session.username = "test_user"
        mock_context.session_manager.create_session.return_value = mock_session
        
        result = await handler.execute(
            host="test.host.com",
            username="test_user",
            auth={"password": "secret_password"}
        )
        
        assert result["success"] is True
        # Verify password was passed to session
        mock_session.connect.assert_called_once_with("password", password="secret_password")

class TestSSHRunHandler:
    """Test SSH command execution handler."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock tool context."""
        context = Mock(spec=ToolContext)
        return context
    
    @pytest.fixture
    def handler(self, mock_context):
        """Create an SSH run handler."""
        return SSHRunHandler(mock_context)
    
    def test_validate_parameters_with_valid_params(self, handler):
        """Test parameter validation with valid parameters."""
        error = handler.validate_parameters(session_id="test_session", cmd="ls -la")
        assert error is None
    
    def test_validate_parameters_without_session_id(self, handler):
        """Test parameter validation without session_id."""
        error = handler.validate_parameters(cmd="ls -la")
        assert "session_id is required" in error
    
    def test_validate_parameters_without_cmd(self, handler):
        """Test parameter validation without cmd."""
        error = handler.validate_parameters(session_id="test_session")
        assert "cmd is required" in error
    
    @pytest.mark.asyncio
    async def test_execute_successful_command(self, handler, mock_context):
        """Test successful command execution."""
        # Mock session and command execution
        mock_session = AsyncMock()
        mock_session.connected = True
        mock_session.execute_command.return_value = Mock(
            stdout="file1.txt\nfile2.txt",
            stderr="",
            exit_status=0,
            duration_ms=100,
            truncated=False
        )
        mock_context.session_manager.get_session.return_value = mock_session
        
        result = await handler.execute(
            session_id="test_session",
            cmd="ls -la"
        )
        
        assert result["success"] is True
        assert result["stdout"] == "file1.txt\nfile2.txt"
        assert result["exit_status"] == 0
        assert result["duration_ms"] == 100
    
    @pytest.mark.asyncio
    async def test_execute_session_not_found(self, handler, mock_context):
        """Test command execution with non-existent session."""
        mock_context.session_manager.get_session.return_value = None
        
        result = await handler.execute(
            session_id="nonexistent_session",
            cmd="ls -la"
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_session_not_connected(self, handler, mock_context):
        """Test command execution with disconnected session."""
        mock_session = Mock()
        mock_session.connected = False
        mock_context.session_manager.get_session.return_value = mock_session
        
        result = await handler.execute(
            session_id="test_session",
            cmd="ls -la"
        )
        
        assert result["success"] is False
        assert "not connected" in result["error"]

class TestSSHDisconnectHandler:
    """Test SSH disconnection handler."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock tool context."""
        context = Mock(spec=ToolContext)
        return context
    
    @pytest.fixture
    def handler(self, mock_context):
        """Create an SSH disconnect handler."""
        return SSHDisconnectHandler(mock_context)
    
    def test_validate_parameters_with_valid_params(self, handler):
        """Test parameter validation with valid parameters."""
        error = handler.validate_parameters(session_id="test_session")
        assert error is None
    
    def test_validate_parameters_without_session_id(self, handler):
        """Test parameter validation without session_id."""
        error = handler.validate_parameters()
        assert "session_id is required" in error
    
    @pytest.mark.asyncio
    async def test_execute_successful_disconnect(self, handler, mock_context):
        """Test successful session disconnection."""
        mock_context.session_manager.remove_session.return_value = True
        
        result = await handler.execute(session_id="test_session")
        
        assert result["success"] is True
        assert result["session_id"] == "test_session"
        assert "disconnected" in result["message"]

class TestSSHListSessionsHandler:
    """Test SSH session listing handler."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock tool context."""
        context = Mock(spec=ToolContext)
        return context
    
    @pytest.fixture
    def handler(self, mock_context):
        """Create an SSH list sessions handler."""
        return SSHListSessionsHandler(mock_context)
    
    def test_validate_parameters_no_params_required(self, handler):
        """Test parameter validation (no parameters required)."""
        error = handler.validate_parameters()
        assert error is None
    
    @pytest.mark.asyncio
    async def test_execute_list_sessions(self, handler, mock_context):
        """Test listing sessions."""
        # Mock session list
        mock_sessions = [
            SessionInfo(
                session_id="session1",
                host="host1.com",
                username="user1",
                connected_at=datetime.now(),
                last_used=datetime.now(),
                current_dir="/home/user1",
                environment={}
            ),
            SessionInfo(
                session_id="session2",
                host="host2.com",
                username="user2",
                connected_at=datetime.now(),
                last_used=datetime.now(),
                current_dir="/home/user2",
                environment={}
            )
        ]
        mock_context.session_manager.list_sessions.return_value = mock_sessions
        
        result = await handler.execute()
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["sessions"]) == 2
        assert result["sessions"][0]["session_id"] == "session1"
        assert result["sessions"][1]["session_id"] == "session2"

class TestToolHandlerFactory:
    """Test the tool handler factory."""
    
    def test_create_handler_ssh_connect(self):
        """Test creating SSH connect handler."""
        factory = ToolHandlerFactory()
        handler = factory.create_handler('ssh_connect')
        assert isinstance(handler, SSHConnectHandler)
    
    def test_create_handler_ssh_run(self):
        """Test creating SSH run handler."""
        factory = ToolHandlerFactory()
        handler = factory.create_handler('ssh_run')
        assert isinstance(handler, SSHRunHandler)
    
    def test_create_handler_ssh_disconnect(self):
        """Test creating SSH disconnect handler."""
        factory = ToolHandlerFactory()
        handler = factory.create_handler('ssh_disconnect')
        assert isinstance(handler, SSHDisconnectHandler)
    
    def test_create_handler_ssh_list_sessions(self):
        """Test creating SSH list sessions handler."""
        factory = ToolHandlerFactory()
        handler = factory.create_handler('ssh_list_sessions')
        assert isinstance(handler, SSHListSessionsHandler)
    
    def test_create_handler_unknown_tool(self):
        """Test creating handler for unknown tool."""
        factory = ToolHandlerFactory()
        with pytest.raises(ValueError, match="Unknown tool"):
            factory.create_handler('unknown_tool')

class TestToolHandlerIntegration:
    """Integration tests for tool handlers."""
    
    @pytest.mark.asyncio
    async def test_connect_and_run_command_flow(self):
        """Test the complete flow of connecting and running a command."""
        factory = ToolHandlerFactory()
        
        # Mock the context to avoid actual SSH connections
        with patch('mcp_remote_ssh.tool_handlers.get_config') as mock_get_config, \
             patch('mcp_remote_ssh.tool_handlers.get_session_manager') as mock_get_session_manager, \
             patch('mcp_remote_ssh.tool_handlers.get_security_manager') as mock_get_security_manager:
            
            # Setup mocks
            mock_config = Mock()
            mock_config.ssh.default_host = "test.host.com"
            mock_config.ssh.default_port = 22
            mock_config.ssh.default_username = "test_user"
            mock_get_config.return_value = mock_config
            
            mock_session_manager = Mock()
            mock_get_session_manager.return_value = mock_session_manager
            
            mock_security_manager = Mock()
            mock_get_security_manager.return_value = mock_security_manager
            
            # Create handlers
            connect_handler = factory.create_handler('ssh_connect')
            run_handler = factory.create_handler('ssh_run')
            
            # Mock session creation and connection
            mock_session = AsyncMock()
            mock_session.username = "test_user"
            mock_session.connected = True
            mock_session.execute_command.return_value = Mock(
                stdout="command output",
                stderr="",
                exit_status=0,
                duration_ms=50,
                truncated=False
            )
            mock_session_manager.create_session.return_value = mock_session
            mock_session_manager.get_session.return_value = mock_session
            
            # Test connection
            connect_result = await connect_handler.execute(
                host="test.host.com",
                username="test_user",
                session_id="test_session"
            )
            
            assert connect_result["success"] is True
            assert connect_result["session_id"] == "test_session"
            
            # Test command execution
            run_result = await run_handler.execute(
                session_id="test_session",
                cmd="echo hello"
            )
            
            assert run_result["success"] is True
            assert run_result["stdout"] == "command output"
            assert run_result["exit_status"] == 0

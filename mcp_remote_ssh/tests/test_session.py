"""Tests for session management."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from mcp_remote_ssh.session import SSHSession, SessionManager, CommandResult

@pytest.fixture
def session_manager():
    return SessionManager()

@pytest.fixture
def ssh_session():
    return SSHSession("test-session", "localhost", 22, "testuser")

class TestSSHSession:
    """Test SSH session functionality."""
    
    @pytest.mark.asyncio
    async def test_session_creation(self, ssh_session):
        """Test SSH session creation."""
        assert ssh_session.session_id == "test-session"
        assert ssh_session.host == "localhost"
        assert ssh_session.port == 22
        assert ssh_session.username == "testuser"
        assert ssh_session.connected is False
    
    @pytest.mark.asyncio
    async def test_session_info(self, ssh_session):
        """Test session info retrieval."""
        info = ssh_session.get_info()
        assert info.session_id == "test-session"
        assert info.host == "localhost"
        assert info.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_command_validation(self, ssh_session):
        """Test that commands are validated before execution."""
        # Mock the session as connected
        ssh_session.connected = True
        ssh_session.channel = Mock()
        
        # Test with invalid command - should raise exception
        with pytest.raises(Exception) as exc_info:
            await ssh_session.execute_command("rm -rf /")
        
        assert "not allowed" in str(exc_info.value).lower()
    
    def test_output_cleaning(self, ssh_session):
        """Test output cleaning functionality."""
        raw_output = """
        $ ls -la
        total 12
        drwxr-xr-x 3 user user 4096 Jan 1 12:00 .
        drwxr-xr-x 5 user user 4096 Jan 1 11:00 ..
        -rw-r--r-- 1 user user  123 Jan 1 12:00 file.txt
        $ 
        """
        
        cleaned = ssh_session._clean_output(raw_output)
        
        # Should not contain prompts or empty lines
        assert "$ ls -la" not in cleaned
        assert "$ " not in cleaned
        assert "total 12" in cleaned
        assert "file.txt" in cleaned

class TestSessionManager:
    """Test session manager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test session creation."""
        session = await session_manager.create_session(
            "test-id", "localhost", 22, "testuser"
        )
        
        assert session.session_id == "test-id"
        assert session.host == "localhost"
        assert session.username == "testuser"
        assert "test-id" in session_manager.sessions
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test session retrieval."""
        # Create a session
        await session_manager.create_session("test-id", "localhost", 22, "testuser")
        
        # Retrieve it
        session = session_manager.get_session("test-id")
        assert session is not None
        assert session.session_id == "test-id"
        
        # Try to get non-existent session
        non_existent = session_manager.get_session("non-existent")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_remove_session(self, session_manager):
        """Test session removal."""
        # Create a session
        session = await session_manager.create_session("test-id", "localhost", 22, "testuser")
        
        # Mock the disconnect method
        session.disconnect = AsyncMock()
        
        # Remove the session
        await session_manager.remove_session("test-id")
        
        # Verify it's gone
        assert "test-id" not in session_manager.sessions
        assert session.disconnect.called
    
    @pytest.mark.asyncio
    async def test_max_sessions_limit(self, session_manager):
        """Test that session limit is enforced."""
        # Mock config to have low limit
        with patch('mcp_remote_ssh.session.get_config') as mock_config:
            mock_config.return_value.security.max_sessions = 2
            
            # Create sessions up to limit
            session1 = await session_manager.create_session("s1", "host1", 22, "user1")
            session2 = await session_manager.create_session("s2", "host2", 22, "user2")
            
            # Mock disconnect for cleanup
            session1.disconnect = AsyncMock()
            session2.disconnect = AsyncMock()
            
            # Creating third session should remove oldest
            session3 = await session_manager.create_session("s3", "host3", 22, "user3")
            
            # Should have removed oldest session
            assert len(session_manager.sessions) <= 2
            assert "s3" in session_manager.sessions
    
    def test_list_sessions(self, session_manager):
        """Test session listing."""
        # Initially empty
        sessions = session_manager.list_sessions()
        assert len(sessions) == 0

class TestCommandResult:
    """Test command result data structure."""
    
    def test_command_result_creation(self):
        """Test command result creation."""
        result = CommandResult(
            stdout="output",
            stderr="error", 
            exit_status=0,
            duration_ms=100,
            truncated=False,
            session_id="test"
        )
        
        assert result.stdout == "output"
        assert result.stderr == "error"
        assert result.exit_status == 0
        assert result.duration_ms == 100
        assert result.truncated is False
        assert result.session_id == "test"

@pytest.mark.integration
class TestIntegration:
    """Integration tests (require actual SSH access)."""
    
    @pytest.mark.skip(reason="Requires SSH server setup")
    @pytest.mark.asyncio
    async def test_real_ssh_connection(self):
        """Test actual SSH connection (skipped by default)."""
        # This test would require a real SSH server
        # Enable only when you have a test environment set up
        session = SSHSession("integration-test", "localhost", 22, "testuser")
        
        # Would test actual connection here
        # success = await session.connect("password", password="testpass")
        # assert success is True
        pass

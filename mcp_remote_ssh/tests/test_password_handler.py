"""Tests for password handling module."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from mcp_remote_ssh.password_handler import (
    PasswordHandler, SudoPasswordHandler, InteractivePasswordHandler,
    PasswordManager, create_password_manager, PasswordPrompt, PasswordResponse
)

class TestSudoPasswordHandler:
    """Test SudoPasswordHandler functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create a SudoPasswordHandler instance."""
        return SudoPasswordHandler("test_password")
    
    @pytest.fixture
    def handler_no_password(self):
        """Create a SudoPasswordHandler instance without password."""
        return SudoPasswordHandler()
    
    def test_can_handle_sudo(self, handler):
        """Test that handler can handle sudo prompts."""
        assert handler.can_handle("sudo") is True
        assert handler.can_handle("ssh") is False
        assert handler.can_handle("login") is False
    
    @pytest.mark.asyncio
    async def test_detect_sudo_prompt(self, handler):
        """Test detection of sudo password prompts."""
        # Test standard sudo prompt
        output = "some output\n[sudo] password for user:"
        prompt = await handler.detect_prompt(output)
        assert prompt is not None
        assert prompt.prompt_type == "sudo"
        assert "password for user" in prompt.prompt_text
        
        # Test simple password prompt
        output = "some output\nPassword:"
        prompt = await handler.detect_prompt(output)
        assert prompt is not None
        assert prompt.prompt_type == "sudo"
        
        # Test terminal required message
        output = "sudo: a terminal is required to read the password"
        prompt = await handler.detect_prompt(output)
        assert prompt is not None
        assert prompt.prompt_type == "sudo"
        
        # Test no prompt
        output = "just some regular output"
        prompt = await handler.detect_prompt(output)
        assert prompt is None
    
    @pytest.mark.asyncio
    async def test_handle_sudo_prompt_with_password(self, handler):
        """Test handling sudo prompt when password is provided."""
        prompt = PasswordPrompt(
            prompt_type="sudo",
            prompt_text="[sudo] password for user:",
            position=0
        )
        context = {"session_id": "test_session"}
        
        response = await handler.handle_prompt(prompt, context)
        assert response.password == "test_password"
        assert response.error is None
        assert response.timeout is False
        assert response.cancelled is False
    
    @pytest.mark.asyncio
    async def test_handle_sudo_prompt_without_password(self, handler_no_password):
        """Test handling sudo prompt when no password is provided."""
        prompt = PasswordPrompt(
            prompt_type="sudo",
            prompt_text="[sudo] password for user:",
            position=0
        )
        context = {"session_id": "test_session"}
        
        response = await handler_no_password.handle_prompt(prompt, context)
        assert response.password is None
        assert "not provided" in response.error
        assert response.timeout is False
        assert response.cancelled is False
    
    @pytest.mark.asyncio
    async def test_handle_wrong_prompt_type(self, handler):
        """Test handling wrong prompt type."""
        prompt = PasswordPrompt(
            prompt_type="ssh",
            prompt_text="ssh password:",
            position=0
        )
        context = {"session_id": "test_session"}
        
        response = await handler.handle_prompt(prompt, context)
        assert response.password is None
        assert "Cannot handle prompt type" in response.error

class TestInteractivePasswordHandler:
    """Test InteractivePasswordHandler functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create an InteractivePasswordHandler instance."""
        return InteractivePasswordHandler()
    
    def test_can_handle_interactive(self, handler):
        """Test that handler can handle interactive prompts."""
        assert handler.can_handle("interactive") is True
        assert handler.can_handle("ssh") is True
        assert handler.can_handle("login") is True
        assert handler.can_handle("sudo") is False
    
    @pytest.mark.asyncio
    async def test_detect_interactive_prompt(self, handler):
        """Test detection of interactive prompts (not implemented)."""
        output = "some output"
        prompt = await handler.detect_prompt(output)
        assert prompt is None
    
    @pytest.mark.asyncio
    async def test_handle_interactive_prompt(self, handler):
        """Test handling interactive prompt (not implemented)."""
        prompt = PasswordPrompt(
            prompt_type="interactive",
            prompt_text="Enter password:",
            position=0
        )
        context = {"session_id": "test_session"}
        
        response = await handler.handle_prompt(prompt, context)
        assert response.password is None
        assert "not implemented" in response.error

class TestPasswordManager:
    """Test PasswordManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a PasswordManager instance."""
        return PasswordManager()
    
    @pytest.fixture
    def sudo_handler(self):
        """Create a SudoPasswordHandler instance."""
        return SudoPasswordHandler("test_password")
    
    @pytest.fixture
    def interactive_handler(self):
        """Create an InteractivePasswordHandler instance."""
        return InteractivePasswordHandler()
    
    def test_add_handler(self, manager, sudo_handler):
        """Test adding a handler."""
        assert len(manager.handlers) == 0
        manager.add_handler(sudo_handler)
        assert len(manager.handlers) == 1
        assert sudo_handler in manager.handlers
    
    def test_remove_handler(self, manager, sudo_handler):
        """Test removing a handler."""
        manager.add_handler(sudo_handler)
        assert len(manager.handlers) == 1
        
        manager.remove_handler(sudo_handler)
        assert len(manager.handlers) == 0
        assert sudo_handler not in manager.handlers
    
    def test_get_handler_for_type(self, manager, sudo_handler, interactive_handler):
        """Test getting handler for specific type."""
        manager.add_handler(sudo_handler)
        manager.add_handler(interactive_handler)
        
        # Test sudo handler
        handler = manager.get_handler_for_type("sudo")
        assert handler is sudo_handler
        
        # Test interactive handler
        handler = manager.get_handler_for_type("interactive")
        assert handler is interactive_handler
        
        # Test non-existent type
        handler = manager.get_handler_for_type("nonexistent")
        assert handler is None
    
    @pytest.mark.asyncio
    async def test_detect_and_handle_prompt(self, manager, sudo_handler):
        """Test detecting and handling prompts."""
        manager.add_handler(sudo_handler)
        
        # Test with sudo prompt
        output = "some output\n[sudo] password for user:"
        context = {"session_id": "test_session"}
        
        response = await manager.detect_and_handle_prompt(output, context)
        assert response is not None
        assert response.password == "test_password"
        
        # Test with no prompt
        output = "just regular output"
        response = await manager.detect_and_handle_prompt(output, context)
        assert response is None
    
    @pytest.mark.asyncio
    async def test_detect_and_handle_prompt_no_handlers(self, manager):
        """Test detecting prompts with no handlers."""
        output = "some output\n[sudo] password for user:"
        context = {"session_id": "test_session"}
        
        response = await manager.detect_and_handle_prompt(output, context)
        assert response is None

class TestCreatePasswordManager:
    """Test factory function for creating password managers."""
    
    def test_create_with_sudo_password(self):
        """Test creating manager with sudo password."""
        manager = create_password_manager("test_password")
        assert len(manager.handlers) == 1
        assert isinstance(manager.handlers[0], SudoPasswordHandler)
        assert manager.handlers[0].sudo_password == "test_password"
    
    def test_create_without_sudo_password(self):
        """Test creating manager without sudo password."""
        manager = create_password_manager()
        assert len(manager.handlers) == 0
    
    def test_create_with_none_sudo_password(self):
        """Test creating manager with None sudo password."""
        manager = create_password_manager(None)
        assert len(manager.handlers) == 0

class TestPasswordPrompt:
    """Test PasswordPrompt dataclass."""
    
    def test_password_prompt_creation(self):
        """Test creating a PasswordPrompt instance."""
        prompt = PasswordPrompt(
            prompt_type="sudo",
            prompt_text="[sudo] password for user:",
            position=10,
            requires_input=True
        )
        
        assert prompt.prompt_type == "sudo"
        assert prompt.prompt_text == "[sudo] password for user:"
        assert prompt.position == 10
        assert prompt.requires_input is True
    
    def test_password_prompt_defaults(self):
        """Test PasswordPrompt with default values."""
        prompt = PasswordPrompt(
            prompt_type="sudo",
            prompt_text="Password:",
            position=0
        )
        
        assert prompt.requires_input is True

class TestPasswordResponse:
    """Test PasswordResponse dataclass."""
    
    def test_password_response_creation(self):
        """Test creating a PasswordResponse instance."""
        response = PasswordResponse(
            password="test_password",
            timeout=False,
            cancelled=False,
            error=None
        )
        
        assert response.password == "test_password"
        assert response.timeout is False
        assert response.cancelled is False
        assert response.error is None
    
    def test_password_response_with_error(self):
        """Test PasswordResponse with error."""
        response = PasswordResponse(
            password=None,
            timeout=False,
            cancelled=False,
            error="Password not provided"
        )
        
        assert response.password is None
        assert response.error == "Password not provided"
    
    def test_password_response_defaults(self):
        """Test PasswordResponse with default values."""
        response = PasswordResponse()
        
        assert response.password is None
        assert response.timeout is False
        assert response.cancelled is False
        assert response.error is None

# Integration tests
class TestPasswordHandlerIntegration:
    """Integration tests for password handling."""
    
    @pytest.mark.asyncio
    async def test_full_sudo_workflow(self):
        """Test complete sudo password handling workflow."""
        # Create manager with sudo password
        manager = create_password_manager("test_password")
        
        # Simulate output with sudo prompt
        output = "some command output\n[sudo] password for user:"
        context = {"session_id": "test_session", "command": "sudo whoami"}
        
        # Detect and handle prompt
        response = await manager.detect_and_handle_prompt(output, context)
        
        # Verify response
        assert response is not None
        assert response.password == "test_password"
        assert response.error is None
    
    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        """Test manager with multiple handlers."""
        manager = PasswordManager()
        
        # Add sudo handler
        sudo_handler = SudoPasswordHandler("sudo_pass")
        manager.add_handler(sudo_handler)
        
        # Add interactive handler
        interactive_handler = InteractivePasswordHandler()
        manager.add_handler(interactive_handler)
        
        assert len(manager.handlers) == 2
        
        # Test sudo prompt
        output = "some output\n[sudo] password for user:"
        context = {"session_id": "test_session"}
        
        response = await manager.detect_and_handle_prompt(output, context)
        assert response is not None
        assert response.password == "sudo_pass"
        
        # Test that interactive handler doesn't interfere
        assert manager.get_handler_for_type("sudo") is sudo_handler
        assert manager.get_handler_for_type("interactive") is interactive_handler

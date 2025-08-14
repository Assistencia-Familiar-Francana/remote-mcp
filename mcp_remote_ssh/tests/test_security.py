"""Tests for security module."""

import pytest
from mcp_remote_ssh.security import SecurityManager, CommandValidationResult

@pytest.fixture
def security_manager():
    return SecurityManager()

class TestCommandValidation:
    """Test command validation logic."""
    
    def test_allowed_command(self, security_manager):
        """Test that allowed commands pass validation."""
        result = security_manager.validate_command("ls -la")
        assert result.allowed is True
        assert "ls" in result.reason or "allowed" in result.reason.lower()
    
    def test_denied_command(self, security_manager):
        """Test that denied commands are rejected."""
        result = security_manager.validate_command("rm -rf /")
        assert result.allowed is False
        assert "denied" in result.reason.lower()
    
    def test_unknown_command(self, security_manager):
        """Test that unknown commands are rejected."""
        result = security_manager.validate_command("unknowncommand123")
        assert result.allowed is False
        assert "not in allowed list" in result.reason
    
    def test_empty_command(self, security_manager):
        """Test that empty commands are rejected."""
        result = security_manager.validate_command("")
        assert result.allowed is False
        assert "empty" in result.reason.lower()
    
    def test_dangerous_patterns(self, security_manager):
        """Test that dangerous patterns are detected."""
        dangerous_commands = [
            "ls && rm file",
            "cat file | sh",
            "ls; rm file",
            "echo `whoami`",
            "ls > /etc/passwd"
        ]
        
        for cmd in dangerous_commands:
            result = security_manager.validate_command(cmd)
            assert result.allowed is False, f"Command should be rejected: {cmd}"
    
    def test_kubectl_validation(self, security_manager):
        """Test kubectl command argument validation."""
        valid_kubectl_commands = [
            "kubectl get pods",
            "kubectl describe service myservice",
            "kubectl logs mypod",
            "kubectl top nodes"
        ]
        
        for cmd in valid_kubectl_commands:
            result = security_manager.validate_command(cmd)
            assert result.allowed is True, f"Command should be allowed: {cmd}"
    
    def test_systemctl_validation(self, security_manager):
        """Test systemctl command argument validation."""
        valid_systemctl_commands = [
            "systemctl status nginx",
            "systemctl is-active docker",
            "systemctl list-units --type=service"
        ]
        
        for cmd in valid_systemctl_commands:
            result = security_manager.validate_command(cmd)
            assert result.allowed is True, f"Command should be allowed: {cmd}"

class TestSecretRedaction:
    """Test secret redaction functionality."""
    
    def test_redact_tokens(self, security_manager):
        """Test that tokens are redacted."""
        text_with_secrets = """
        API_KEY=sk-1234567890abcdef1234567890abcdef12345678
        GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
        Some normal text here
        """
        
        redacted = security_manager.redact_secrets(text_with_secrets)
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in redacted
        assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in redacted
        assert "[REDACTED_API_KEY]" in redacted
        assert "[REDACTED_GITHUB_TOKEN]" in redacted
        assert "Some normal text here" in redacted
    
    def test_redact_private_keys(self, security_manager):
        """Test that private keys are redacted."""
        text_with_key = """
        -----BEGIN PRIVATE KEY-----
        MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7...
        -----END PRIVATE KEY-----
        """
        
        redacted = security_manager.redact_secrets(text_with_key)
        assert "-----BEGIN PRIVATE KEY-----" not in redacted
        assert "[REDACTED_PRIVATE_KEY]" in redacted

class TestPathValidation:
    """Test file path validation."""
    
    def test_allowed_paths(self, security_manager):
        """Test that allowed paths pass validation."""
        allowed_paths = [
            "/home/user/file.txt",
            "/var/log/app.log", 
            "/tmp/tempfile",
            "./local-file",
            "../parent-file"
        ]
        
        for path in allowed_paths:
            result = security_manager.validate_file_path(path)
            assert result.allowed is True, f"Path should be allowed: {path}"
    
    def test_dangerous_paths(self, security_manager):
        """Test that dangerous paths are rejected."""
        dangerous_paths = [
            "/etc/passwd",
            "/proc/version",
            "/sys/kernel",
            "/dev/null",
            "/boot/grub",
            "~/.ssh/id_rsa",
            "/root/.bashrc",
            "../../../etc/passwd"
        ]
        
        for path in dangerous_paths:
            result = security_manager.validate_file_path(path)
            assert result.allowed is False, f"Path should be rejected: {path}"
    
    def test_empty_path(self, security_manager):
        """Test that empty paths are rejected."""
        result = security_manager.validate_file_path("")
        assert result.allowed is False
        assert "empty" in result.reason.lower()

class TestLoggingSafety:
    """Test logging safety features."""
    
    def test_should_log_command(self, security_manager):
        """Test command logging decisions."""
        # Safe to log
        assert security_manager.should_log_command("ls -la") is True
        assert security_manager.should_log_command("kubectl get pods") is True
        
        # Should not log
        assert security_manager.should_log_command("passwd user") is False
        assert security_manager.should_log_command("sudo something") is False
        assert security_manager.should_log_command("ssh user@host") is False

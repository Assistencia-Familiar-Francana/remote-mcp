"""Security utilities for command validation and sanitization."""

import shlex
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .config import get_config
from .security_patterns import SecurityPatternManager

logger = logging.getLogger(__name__)

@dataclass
class CommandValidationResult:
    """Result of command validation."""
    allowed: bool
    reason: str
    sanitized_cmd: Optional[str] = None

class SecurityManager:
    """Manages command security validation and sanitization."""
    
    def __init__(self):
        self.config = get_config().security
        self.pattern_manager = SecurityPatternManager()
    
    def validate_command(self, command: str) -> CommandValidationResult:
        """Validate if a command is allowed to run."""
        if not command or not command.strip():
            return CommandValidationResult(False, "Empty command")
        
        try:
            # Parse command safely
            parts = shlex.split(command.strip())
            if not parts:
                return CommandValidationResult(False, "Invalid command syntax")
            
            cmd_name = parts[0]
            
            # Check if command is explicitly denied (but allow sudo for K8s administration)
            if cmd_name in self.config.denied_commands and cmd_name != "sudo":
                return CommandValidationResult(False, f"Command '{cmd_name}' is explicitly denied")
            
            # Check if command is in allowed list
            if cmd_name not in self.config.allowed_commands:
                return CommandValidationResult(False, f"Command '{cmd_name}' is not in allowed list")
            
            # Additional validation for specific commands
            args_string = ' '.join(parts[1:])
            if not self.pattern_manager.validate_command_args(cmd_name, args_string):
                return CommandValidationResult(False, f"Unsafe arguments for command '{cmd_name}'")
            
            # Check for dangerous patterns
            dangerous_matches = self.pattern_manager.check_dangerous_patterns(command)
            if dangerous_matches:
                pattern_name = dangerous_matches[0].pattern_name
                return CommandValidationResult(False, f"Dangerous pattern detected: {pattern_name}")
            
            # Sanitize the command
            sanitized = self._sanitize_command(command)
            
            return CommandValidationResult(True, "Command allowed", sanitized)
            
        except ValueError as e:
            return CommandValidationResult(False, f"Command parsing error: {e}")
    
    def _validate_command_args(self, cmd_name: str, args: str) -> bool:
        """Validate arguments for specific commands."""
        return self.pattern_manager.validate_command_args(cmd_name, args)
    
    def _sanitize_command(self, command: str) -> str:
        """Sanitize command by removing/replacing dangerous elements."""
        sanitized = command.strip()
        
        # Remove any null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Limit command length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def redact_secrets(self, text: str) -> str:
        """Redact potential secrets from text."""
        return self.pattern_manager.redact_secrets(text)
    
    def should_log_command(self, command: str) -> bool:
        """Determine if command should be logged (avoid logging sensitive commands)."""
        sensitive_commands = ['passwd', 'su', 'sudo', 'ssh', 'scp']
        cmd_name = command.strip().split()[0] if command.strip() else ''
        
        return cmd_name.lower() not in sensitive_commands
    
    def validate_file_path(self, path: str) -> CommandValidationResult:
        """Validate file path for upload/download operations."""
        if not path or not path.strip():
            return CommandValidationResult(False, "Empty path")
        
        path = path.strip()
        
        # Dangerous path patterns
        dangerous_patterns = [
            r'\.\./',  # Directory traversal
            r'/etc/',  # System config
            r'/proc/',  # Process info
            r'/sys/',  # System info
            r'/dev/',  # Device files
            r'/boot/',  # Boot files
            r'~/.ssh/',  # SSH keys
            r'/root/',  # Root directory
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return CommandValidationResult(False, f"Dangerous path pattern: {pattern}")
        
        # Only allow certain directories
        allowed_prefixes = [
            '/home/',
            '/var/log/',
            '/tmp/',
            '/opt/',
            '/usr/local/',
            './',
            '../',  # Limited traversal
        ]
        
        if not any(path.startswith(prefix) for prefix in allowed_prefixes):
            return CommandValidationResult(False, "Path not in allowed directories")
        
        return CommandValidationResult(True, "Path allowed", path)

# Global security manager instance
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    return security_manager

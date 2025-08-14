"""Security utilities for command validation and sanitization."""

import re
import shlex
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .config import get_config

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
        
        # Patterns for secret detection and redaction
        self.secret_patterns = [
            (re.compile(r'[A-Za-z0-9+/]{40,}={0,2}', re.IGNORECASE), '[REDACTED_TOKEN]'),  # Base64-like tokens
            (re.compile(r'sk-[A-Za-z0-9]{48}', re.IGNORECASE), '[REDACTED_API_KEY]'),    # OpenAI-style keys
            (re.compile(r'ghp_[A-Za-z0-9]{36}', re.IGNORECASE), '[REDACTED_GITHUB_TOKEN]'),  # GitHub tokens
            (re.compile(r'glpat-[A-Za-z0-9_\-]{20}', re.IGNORECASE), '[REDACTED_GITLAB_TOKEN]'),  # GitLab tokens
            (re.compile(r'xox[baprs]-[A-Za-z0-9\-]{10,48}', re.IGNORECASE), '[REDACTED_SLACK_TOKEN]'),  # Slack tokens
            (re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE), '[REDACTED_AWS_KEY]'),      # AWS access keys
            (re.compile(r'-----BEGIN [A-Z ]+-----.*?-----END [A-Z ]+-----', re.DOTALL), '[REDACTED_PRIVATE_KEY]'),  # PEM keys
        ]
        
        # Safe argument patterns for allowed commands
        self.safe_arg_patterns = {
            'kubectl': [
                r'^get\s+(pods?|services?|deployments?|nodes?|namespaces?)(\s+\S+)*(\s+-[a-zA-Z]+(\s+\S+)*)*$',
                r'^describe\s+(pods?|services?|deployments?|nodes?)(\s+\S+)*(\s+-[a-zA-Z]+(\s+\S+)*)*$',
                r'^logs\s+\S+(\s+-[a-zA-Z]+(\s+\S+)*)*$',
                r'^top\s+(pods?|nodes?)(\s+-[a-zA-Z]+(\s+\S+)*)*$',
                r'^config\s+view(\s+--minify)?$',
            ],
            'systemctl': [
                r'^status\s+\S+$',
                r'^is-active\s+\S+$',
                r'^is-enabled\s+\S+$',
                r'^list-units(\s+--type=\w+)?(\s+--state=\w+)?$',
            ],
            'journalctl': [
                r'^--since\s+"[^"]*"(\s+--unit=\S+)?(\s+-n\s+\d+)?$',
                r'^--unit=\S+(\s+--since\s+"[^"]*")?(\s+-n\s+\d+)?$',
                r'^-n\s+\d+(\s+--unit=\S+)?$',
            ],
            'docker': [
                r'^ps(\s+-[a-zA-Z]+)*$',
                r'^images(\s+-[a-zA-Z]+)*$',
                r'^logs\s+\S+(\s+-[a-zA-Z]+(\s+\S+)*)*$',
                r'^inspect\s+\S+$',
                r'^stats(\s+\S+)*$',
            ],
            'git': [
                r'^status$',
                r'^log(\s+--oneline)?(\s+-n\s+\d+)?$',
                r'^branch(\s+-[a-zA-Z]+)*$',
                r'^diff(\s+\S+)*$',
                r'^show(\s+\S+)*$',
            ]
        }
    
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
            
            # Check if command is explicitly denied
            if cmd_name in self.config.denied_commands:
                return CommandValidationResult(False, f"Command '{cmd_name}' is explicitly denied")
            
            # Check if command is in allowed list
            if cmd_name not in self.config.allowed_commands:
                return CommandValidationResult(False, f"Command '{cmd_name}' is not in allowed list")
            
            # Additional validation for specific commands
            if cmd_name in self.safe_arg_patterns:
                args_string = ' '.join(parts[1:])
                if not self._validate_command_args(cmd_name, args_string):
                    return CommandValidationResult(False, f"Unsafe arguments for command '{cmd_name}'")
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r'&&', r'\|\|', r';', r'\|', r'`', r'\$\(',  # Command chaining
                r'>', r'>>', r'<',  # Redirection
                r'\*', r'\?', r'\[', r'\]',  # Glob patterns (in some contexts)
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    return CommandValidationResult(False, f"Dangerous pattern detected: {pattern}")
            
            # Sanitize the command
            sanitized = self._sanitize_command(command)
            
            return CommandValidationResult(True, "Command allowed", sanitized)
            
        except ValueError as e:
            return CommandValidationResult(False, f"Command parsing error: {e}")
    
    def _validate_command_args(self, cmd_name: str, args: str) -> bool:
        """Validate arguments for specific commands."""
        patterns = self.safe_arg_patterns.get(cmd_name, [])
        if not patterns:
            return True  # No specific validation rules
        
        for pattern in patterns:
            if re.match(pattern, args, re.IGNORECASE):
                return True
        
        return False
    
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
        if not text:
            return text
        
        result = text
        for pattern, replacement in self.secret_patterns:
            result = pattern.sub(replacement, result)
        
        return result
    
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

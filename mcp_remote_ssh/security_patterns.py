"""Security patterns management following SOLID principles."""

import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PatternMatch:
    """Result of a pattern match."""
    matched: bool
    pattern_name: str
    replacement: Optional[str] = None
    position: Optional[int] = None

class SecurityPattern(ABC):
    """Abstract base class for security patterns."""
    
    def __init__(self, name: str, pattern: str, replacement: Optional[str] = None):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.replacement = replacement
    
    @abstractmethod
    def match(self, text: str) -> PatternMatch:
        """Match the pattern against text."""
        pass
    
    @abstractmethod
    def is_dangerous(self) -> bool:
        """Check if this pattern represents a dangerous operation."""
        pass

class SecretPattern(SecurityPattern):
    """Pattern for detecting and redacting secrets."""
    
    def __init__(self, name: str, pattern: str, replacement: str):
        super().__init__(name, pattern, replacement)
    
    def match(self, text: str) -> PatternMatch:
        """Match secret pattern and return replacement."""
        match = self.pattern.search(text)
        if match:
            return PatternMatch(
                matched=True,
                pattern_name=self.name,
                replacement=self.replacement,
                position=match.start()
            )
        return PatternMatch(matched=False, pattern_name=self.name)
    
    def is_dangerous(self) -> bool:
        """Secret patterns are not dangerous, they're for redaction."""
        return False

class DangerousPattern(SecurityPattern):
    """Pattern for detecting dangerous operations."""
    
    def __init__(self, name: str, pattern: str):
        super().__init__(name, pattern)
    
    def match(self, text: str) -> PatternMatch:
        """Match dangerous pattern."""
        match = self.pattern.search(text)
        if match:
            return PatternMatch(
                matched=True,
                pattern_name=self.name,
                position=match.start()
            )
        return PatternMatch(matched=False, pattern_name=self.name)
    
    def is_dangerous(self) -> bool:
        """Dangerous patterns are dangerous by definition."""
        return True

class CommandPattern(SecurityPattern):
    """Pattern for validating command arguments."""
    
    def __init__(self, name: str, pattern: str):
        super().__init__(name, pattern)
    
    def match(self, text: str) -> PatternMatch:
        """Match command pattern."""
        match = self.pattern.match(text)
        if match:
            return PatternMatch(
                matched=True,
                pattern_name=self.name
            )
        return PatternMatch(matched=False, pattern_name=self.name)
    
    def is_dangerous(self) -> bool:
        """Command patterns are not dangerous, they're for validation."""
        return False

class SecurityPatternManager:
    """Manages security patterns following Single Responsibility Principle."""
    
    def __init__(self):
        self.secret_patterns: List[SecretPattern] = []
        self.dangerous_patterns: List[DangerousPattern] = []
        self.command_patterns: Dict[str, List[CommandPattern]] = {}
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize all security patterns."""
        self._initialize_secret_patterns()
        self._initialize_dangerous_patterns()
        self._initialize_command_patterns()
    
    def _initialize_secret_patterns(self) -> None:
        """Initialize secret detection patterns."""
        self.secret_patterns = [
            SecretPattern("base64_token", r'[A-Za-z0-9+/]{40,}={0,2}', '[REDACTED_TOKEN]'),
            SecretPattern("openai_key", r'sk-[A-Za-z0-9]{48}', '[REDACTED_API_KEY]'),
            SecretPattern("github_token", r'ghp_[A-Za-z0-9]{36}', '[REDACTED_GITHUB_TOKEN]'),
            SecretPattern("gitlab_token", r'glpat-[A-Za-z0-9_\-]{20}', '[REDACTED_GITLAB_TOKEN]'),
            SecretPattern("slack_token", r'xox[baprs]-[A-Za-z0-9\-]{10,48}', '[REDACTED_SLACK_TOKEN]'),
            SecretPattern("aws_key", r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY]'),
            SecretPattern("private_key", r'-----BEGIN [A-Z ]+-----.*?-----END [A-Z ]+-----', '[REDACTED_PRIVATE_KEY]'),
        ]
    
    def _initialize_dangerous_patterns(self) -> None:
        """Initialize dangerous operation patterns."""
        self.dangerous_patterns = [
            DangerousPattern("command_chaining", r'&&|\|\||;|\||`|\$\(|>|>>|<|\*|\?|\[|\]'),
            DangerousPattern("rm_rf_root", r'rm\s+-rf\s+/'),
            DangerousPattern("dd_disk_wipe", r'dd\s+if=/dev/zero\s+of=/dev/sd[a-z]'),
            DangerousPattern("mkfs_destruction", r'mkfs\.ext4\s+/dev/sd[a-z]'),
            DangerousPattern("fdisk_destruction", r'fdisk\s+/dev/sd[a-z]'),
        ]
    
    def _initialize_command_patterns(self) -> None:
        """Initialize command validation patterns."""
        self.command_patterns = {
            'kubectl': [
                CommandPattern("kubectl_get", r'^get\s+(pods?|services?|deployments?|nodes?|namespaces?)(\s+\S+)*(\s+-[a-zA-Z]+(\s+\S+)*)*$'),
                CommandPattern("kubectl_describe", r'^describe\s+(pods?|services?|deployments?|nodes?)(\s+\S+)*(\s+-[a-zA-Z]+(\s+\S+)*)*$'),
                CommandPattern("kubectl_logs", r'^logs\s+\S+(\s+-[a-zA-Z]+(\s+\S+)*)*$'),
                CommandPattern("kubectl_top", r'^top\s+(pods?|nodes?)(\s+-[a-zA-Z]+(\s+\S+)*)*$'),
                CommandPattern("kubectl_config", r'^config\s+view(\s+--minify)?$'),
            ],
            'systemctl': [
                CommandPattern("systemctl_status", r'^status\s+\S+$'),
                CommandPattern("systemctl_is_active", r'^is-active\s+\S+$'),
                CommandPattern("systemctl_is_enabled", r'^is-enabled\s+\S+$'),
                CommandPattern("systemctl_list_units", r'^list-units(\s+--type=\w+)?(\s+--state=\w+)?$'),
            ],
            'journalctl': [
                CommandPattern("journalctl_since", r'^--since\s+"[^"]*"(\s+--unit=\S+)?(\s+-n\s+\d+)?$'),
                CommandPattern("journalctl_unit", r'^--unit=\S+(\s+--since\s+"[^"]*")?(\s+-n\s+\d+)?$'),
                CommandPattern("journalctl_lines", r'^-n\s+\d+(\s+--unit=\S+)?$'),
            ],
            'docker': [
                CommandPattern("docker_ps", r'^ps(\s+-[a-zA-Z]+)*$'),
                CommandPattern("docker_images", r'^images(\s+-[a-zA-Z]+)*$'),
                CommandPattern("docker_logs", r'^logs\s+\S+(\s+-[a-zA-Z]+(\s+\S+)*)*$'),
                CommandPattern("docker_inspect", r'^inspect\s+\S+$'),
                CommandPattern("docker_stats", r'^stats(\s+\S+)*$'),
            ],
            'git': [
                CommandPattern("git_status", r'^status$'),
                CommandPattern("git_log", r'^log(\s+--oneline)?(\s+-n\s+\d+)?$'),
                CommandPattern("git_branch", r'^branch(\s+-[a-zA-Z]+)*$'),
                CommandPattern("git_diff", r'^diff(\s+\S+)*$'),
                CommandPattern("git_show", r'^show(\s+\S+)*$'),
            ]
        }
    
    def redact_secrets(self, text: str) -> str:
        """Redact secrets from text using secret patterns."""
        if not text:
            return text
        
        result = text
        for pattern in self.secret_patterns:
            match = pattern.match(result)
            if match.matched and match.replacement:
                result = pattern.pattern.sub(match.replacement, result)
        
        return result
    
    def check_dangerous_patterns(self, text: str) -> List[PatternMatch]:
        """Check for dangerous patterns in text."""
        matches = []
        for pattern in self.dangerous_patterns:
            match = pattern.match(text)
            if match.matched:
                matches.append(match)
        return matches
    
    def validate_command_args(self, command: str, args: str) -> bool:
        """Validate command arguments using command patterns."""
        patterns = self.command_patterns.get(command, [])
        if not patterns:
            return True  # No specific validation rules
        
        for pattern in patterns:
            match = pattern.match(args)
            if match.matched:
                return True
        
        return False
    
    def add_secret_pattern(self, name: str, pattern: str, replacement: str) -> None:
        """Add a new secret pattern."""
        self.secret_patterns.append(SecretPattern(name, pattern, replacement))
    
    def add_dangerous_pattern(self, name: str, pattern: str) -> None:
        """Add a new dangerous pattern."""
        self.dangerous_patterns.append(DangerousPattern(name, pattern))
    
    def add_command_pattern(self, command: str, name: str, pattern: str) -> None:
        """Add a new command validation pattern."""
        if command not in self.command_patterns:
            self.command_patterns[command] = []
        self.command_patterns[command].append(CommandPattern(name, pattern))
    
    def remove_pattern(self, pattern_type: str, name: str) -> bool:
        """Remove a pattern by name."""
        if pattern_type == "secret":
            self.secret_patterns = [p for p in self.secret_patterns if p.name != name]
            return True
        elif pattern_type == "dangerous":
            self.dangerous_patterns = [p for p in self.dangerous_patterns if p.name != name]
            return True
        elif pattern_type == "command":
            for command_patterns in self.command_patterns.values():
                command_patterns[:] = [p for p in command_patterns if p.name != name]
            return True
        return False
    
    def get_pattern_stats(self) -> Dict[str, int]:
        """Get statistics about patterns."""
        return {
            "secret_patterns": len(self.secret_patterns),
            "dangerous_patterns": len(self.dangerous_patterns),
            "command_patterns": sum(len(patterns) for patterns in self.command_patterns.values()),
            "commands_with_patterns": len(self.command_patterns)
        }

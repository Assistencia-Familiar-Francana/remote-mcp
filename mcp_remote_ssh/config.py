"""Configuration management for MCP Remote SSH server."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    allowed_commands: List[str] = field(default_factory=lambda: [
        # File operations
        "ls", "cat", "head", "tail", "grep", "find", "du", "df", "file", "stat",
        # System info
        "uname", "whoami", "id", "pwd", "date", "uptime", "free", "lscpu",
        # Process management
        "ps", "top", "htop", "pgrep", "pidof",
        # Network
        "ping", "curl", "wget", "netstat", "ss", "dig", "nslookup",
        # Kubernetes
        "kubectl", "k9s", "helm",
        # System services
        "systemctl", "journalctl", "service",
        # Text processing
        "awk", "sed", "sort", "uniq", "wc", "cut", "tr",
        # Archive operations
        "tar", "gzip", "gunzip", "zip", "unzip",
        # Git operations
        "git",
        # Docker operations
        "docker", "docker-compose",
        # Tunnels
        "ssh", "scp", "rsync", "tailscale", "tailscaled", "cloudflared"
    ])
    
    denied_commands: List[str] = field(default_factory=lambda: [
        # Dangerous operations
        "rm", "rmdir", "mv", "cp", "dd", "mkfs", "fdisk", "parted",
        # System modification
        "sudo", "su", "passwd", "usermod", "userdel", "useradd",
        # Network services
        "nc", "netcat", "telnet", "ssh", "scp", "rsync",
        # Package management
        "apt", "yum", "dnf", "pacman", "pip", "npm", "gem",
        # Compilation
        "gcc", "g++", "make", "cmake", "cargo", "go",
        # System control
        "reboot", "shutdown", "halt", "poweroff", "init",
        # Process control
        "kill", "killall", "pkill", "nohup",
    ])
    
    max_output_bytes: int = 128 * 1024  # 128KB
    max_output_lines: int = 1000
    command_timeout_seconds: int = 30
    rate_limit_per_minute: int = 60
    max_sessions: int = 5

@dataclass
class SSHConfig:
    """SSH connection configuration."""
    default_host: Optional[str] = None
    default_port: int = 22
    default_username: Optional[str] = None
    key_path: Optional[str] = None
    proxy_command: Optional[str] = None
    connect_timeout: int = 30
    keepalive_interval: int = 30
    
    @classmethod
    def from_env(cls) -> 'SSHConfig':
        """Create SSH config from environment variables."""
        return cls(
            default_host=os.getenv('MCP_SSH_HOST'),
            default_port=int(os.getenv('MCP_SSH_PORT', '22')),
            default_username=os.getenv('MCP_SSH_USER'),
            key_path=os.getenv('MCP_SSH_KEY'),
            proxy_command=os.getenv('MCP_SSH_PROXY_COMMAND'),
            connect_timeout=int(os.getenv('MCP_SSH_CONNECT_TIMEOUT', '30')),
            keepalive_interval=int(os.getenv('MCP_SSH_KEEPALIVE', '30')),
        )

@dataclass
class Config:
    """Main configuration class."""
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ssh: SSHConfig = field(default_factory=SSHConfig.from_env)
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'Config':
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = os.getenv('MCP_SSH_CONFIG', 'mcp_ssh_config.yaml')
        
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            security=SecurityConfig(**data.get('security', {})),
            ssh=SSHConfig(**data.get('ssh', {})),
            debug=data.get('debug', False),
            log_level=data.get('log_level', 'INFO'),
        )

# Global config instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config

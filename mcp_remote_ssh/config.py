"""Configuration management for MCP Remote SSH server."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv
from enum import Enum

# Load environment variables
load_dotenv()

class PermissibilityLevel(Enum):
    """Permission levels for command execution."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    
    @classmethod
    def from_string(cls, value: str) -> 'PermissibilityLevel':
        """Create PermissibilityLevel from string."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MEDIUM  # Default to medium if invalid

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    permissibility_level: PermissibilityLevel = field(
        default_factory=lambda: PermissibilityLevel.from_string(
            os.getenv('MCP_SSH_PERMISSIBILITY_LEVEL', 'medium')
        )
    )
    
    # Low permissibility commands (basic operations only)
    low_permissibility_commands: List[str] = field(default_factory=lambda: [
        # Basic file operations (read-only)
        "ls", "cat", "head", "tail", "grep", "find", "du", "df", "file", "stat",
        
        # Basic system info
        "uname", "whoami", "id", "pwd", "date", "uptime", "free", "lscpu",
        "ps", "top", "htop", "pgrep", "pidof",
        
        # Basic network info
        "ping", "curl", "wget", "netstat", "ss", "dig", "nslookup",
        "ip", "route", "arp", "ifconfig",
        
        # Basic text processing
        "awk", "sed", "sort", "uniq", "wc", "cut", "tr", "echo", "printf",
        
        # Basic utilities
        "which", "whereis", "type", "hash", "env", "export", "unset",
        "history", "cd", "pwd"
    ])
    
    # Medium permissibility commands (includes low + moderate operations)
    medium_permissibility_commands: List[str] = field(default_factory=lambda: [
        # File operations (including write operations)
        "nano", "vim", "vi", "tee", "cp", "mv", "rm", "rmdir", "mkdir", "touch",
        "chmod", "chown", "ln", "chattr", "lsattr",
        
        # System administration (non-destructive)
        "kill", "killall", "pkill", "nohup", "systemctl", "journalctl", "service",
        
        # Network administration
        "iwconfig", "tcpdump", "wireshark",
        
        # Kubernetes administration (read-only and basic operations)
        "kubectl", "k9s", "helm", "k3s", "k3s-agent", "crictl", "ctr",
        
        # Archive operations
        "tar", "gzip", "gunzip", "zip", "unzip", "bzip2", "xz",
        
        # Git operations
        "git",
        
        # Container operations (read-only)
        "docker", "docker-compose", "podman", "buildah",
        
        # Network tunnels and VPNs
        "ssh", "scp", "rsync", "tailscale", "tailscaled", "cloudflared",
        
        # Package management (read-only)
        "apt", "apt-get", "dpkg", "snap", "yum", "dnf", "pacman",
        
        # Monitoring and debugging
        "strace", "ltrace", "gdb", "valgrind", "perf", "iotop", "iostat",
        
        # Hardware and kernel (read-only)
        "lshw", "lspci", "lsusb", "lsmod", "dmesg", "lspcmcia",
        
        # User and group management (read-only)
        "useradd", "usermod", "userdel", "groupadd", "groupmod", "groupdel",
        "passwd", "chpasswd", "newusers", "vipw", "vigr",
        
        # Security and certificates (read-only)
        "openssl", "certbot", "letsencrypt", "ufw", "iptables", "firewall-cmd",
        "ssh-keygen", "ssh-add", "ssh-copy-id",
        
        # Process and system monitoring
        "htop", "iotop", "iftop", "nethogs", "nload", "bmon", "nmtui",
        
        # File system operations (read-only)
        "mount", "umount", "fdisk", "parted", "mkfs", "fsck", "tune2fs",
        
        # Shell and scripting
        "bash", "sh", "zsh", "fish", "screen", "tmux", "nohup",
        
        # Text editors
        "nano", "vim", "vi", "emacs", "joe", "ed", "ex", "view",
        
        # Network tools
        "nc", "netcat", "telnet", "nmap", "traceroute", "mtr", "whois",
        
        # System utilities
        "sync", "swapon", "swapoff", "mkswap", "blkid", "lsblk", "fdisk",
        
        # Log analysis
        "logrotate", "logwatch", "logcheck", "fail2ban", "rsyslog",
        
        # Time and date
        "timedatectl", "ntpdate", "chrony", "systemd-timesyncd",
        
        # Power management
        "upower", "tlp", "powertop", "cpupower", "cpufreq-set",
        
        # All other common commands
        "alias", "unalias", "set", "readonly", "declare", "local", "return", "exit",
        "source", "exec", "eval", "trap", "wait", "jobs", "fg", "bg",
        "fc", "pushd", "popd", "dirs"
    ])
    
    # High permissibility commands (includes medium + sudo and advanced operations)
    high_permissibility_commands: List[str] = field(default_factory=lambda: [
        # Sudo operations
        "sudo", "sudoedit",
        
        # System control (with sudo)
        "reboot", "shutdown", "halt", "poweroff", "init", "systemctl",
        
        # Advanced operations (with sudo)
        "modprobe", "dmesg", "lspcmcia",
        
        # All commands from medium level are included
    ])
    
    # Commands that are always denied regardless of permissibility level
    always_denied_commands: List[str] = field(default_factory=lambda: [
        # Critical system destruction commands
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda",
        "fdisk /dev/sda",
        "mkfs.ext4 /dev/sdX",
        "fdisk /dev/sdX",
        "dd if=/dev/zero of=/dev/sdX",
        "rm -rf /sdX",
    ])
    
    # Pattern restrictions based on permissibility level
    low_permissibility_patterns: List[str] = field(default_factory=lambda: [
        # No command chaining
        r'&&|\|\||;|\||`|\$\(|>|>>|<|\*|\?|\[|\]',
        # No sudo
        r'\bsudo\b',
        # No root operations
        r'rm\s+-rf\s+/',
        r'dd\s+if=/dev/zero\s+of=/dev/sd[a-z]',
        r'mkfs\.ext4\s+/dev/sd[a-z]',
        r'fdisk\s+/dev/sd[a-z]',
    ])
    
    medium_permissibility_patterns: List[str] = field(default_factory=lambda: [
        # Allow some command chaining but not dangerous ones
        r'rm\s+-rf\s+/',
        r'dd\s+if=/dev/zero\s+of=/dev/sd[a-z]',
        r'mkfs\.ext4\s+/dev/sd[a-z]',
        r'fdisk\s+/dev/sd[a-z]',
    ])
    
    high_permissibility_patterns: List[str] = field(default_factory=lambda: [
        # Only block the most dangerous operations
        r'rm\s+-rf\s+/$',  # Only exact match for root deletion
        r'dd\s+if=/dev/zero\s+of=/dev/sd[a-z]$',  # Only exact match for disk wiping
        r'mkfs\.ext4\s+/dev/sd[a-z]$',  # Only exact match for filesystem destruction
        r'fdisk\s+/dev/sd[a-z]$',  # Only exact match for partition destruction
    ])
    
    max_output_bytes: int = 10 * 1024 * 1024  # 10MB (for large logs, configs)
    max_output_lines: int = 10000  # For extensive logs
    command_timeout_seconds: int = 300  # 5 minutes for long operations
    rate_limit_per_minute: int = 500  # High rate for admin tasks
    max_sessions: int = 20  # Many concurrent sessions
    
    def __post_init__(self):
        """Post-initialization to ensure permissibility level is properly set."""
        if isinstance(self.permissibility_level, str):
            self.permissibility_level = PermissibilityLevel.from_string(self.permissibility_level)
    
    def get_allowed_commands(self) -> List[str]:
        """Get allowed commands based on current permissibility level."""
        if self.permissibility_level == PermissibilityLevel.LOW:
            return self.low_permissibility_commands
        elif self.permissibility_level == PermissibilityLevel.MEDIUM:
            return self.low_permissibility_commands + self.medium_permissibility_commands
        elif self.permissibility_level == PermissibilityLevel.HIGH:
            return self.low_permissibility_commands + self.medium_permissibility_commands + self.high_permissibility_commands
        return self.medium_permissibility_commands  # Default fallback
    
    def get_denied_patterns(self) -> List[str]:
        """Get denied patterns based on current permissibility level."""
        if self.permissibility_level == PermissibilityLevel.LOW:
            return self.low_permissibility_patterns
        elif self.permissibility_level == PermissibilityLevel.MEDIUM:
            return self.medium_permissibility_patterns
        elif self.permissibility_level == PermissibilityLevel.HIGH:
            return self.high_permissibility_patterns
        return self.medium_permissibility_patterns  # Default fallback

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
    # Password configuration
    default_password: Optional[str] = None
    sudo_password: Optional[str] = None
    enable_interactive_password: bool = True
    
    @classmethod
    def from_env(cls) -> 'SSHConfig':
        """Create SSH config from environment variables."""
        # Get MCP_PASSWORD as fallback
        mcp_password = os.getenv('MCP_PASSWORD')
        
        # Get specific passwords, with MCP_PASSWORD as fallback
        default_password = os.getenv('MCP_SSH_PASSWORD') or mcp_password
        sudo_password = os.getenv('MCP_SSH_SUDO_PASSWORD') or mcp_password
        
        return cls(
            default_host=os.getenv('MCP_SSH_HOST'),
            default_port=int(os.getenv('MCP_SSH_PORT', '22')),
            default_username=os.getenv('MCP_SSH_USER'),
            key_path=os.getenv('MCP_SSH_KEY'),
            proxy_command=os.getenv('MCP_SSH_PROXY_COMMAND'),
            connect_timeout=int(os.getenv('MCP_SSH_CONNECT_TIMEOUT', '30')),
            keepalive_interval=int(os.getenv('MCP_SSH_KEEPALIVE', '30')),
            # Password configuration from environment with MCP_PASSWORD fallback
            default_password=default_password,
            sudo_password=sudo_password,
            enable_interactive_password=os.getenv('MCP_SSH_INTERACTIVE_PASSWORD', 'true').lower() == 'true',
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

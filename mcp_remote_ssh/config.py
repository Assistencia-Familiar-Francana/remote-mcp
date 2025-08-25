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
        # File operations (including root files)
        "ls", "cat", "head", "tail", "grep", "find", "du", "df", "file", "stat",
        "sudo", "sudoedit", "nano", "vim", "vi", "tee", "cp", "mv", "rm", "rmdir",
        "mkdir", "touch", "chmod", "chown", "ln", "chattr", "lsattr",
        
        # System info and administration
        "uname", "whoami", "id", "pwd", "date", "uptime", "free", "lscpu",
        "ps", "top", "htop", "pgrep", "pidof", "kill", "killall", "pkill", "nohup",
        
        # Network administration
        "ping", "curl", "wget", "netstat", "ss", "dig", "nslookup",
        "ip", "route", "arp", "ifconfig", "iwconfig", "tcpdump", "wireshark",
        
        # Kubernetes administration
        "kubectl", "k9s", "helm", "k3s", "k3s-agent", "crictl", "ctr",
        
        # System services and administration
        "systemctl", "journalctl", "service", "systemd", "init", "telinit",
        
        # Text processing and editing
        "awk", "sed", "sort", "uniq", "wc", "cut", "tr", "echo", "printf",
        
        # Archive operations
        "tar", "gzip", "gunzip", "zip", "unzip", "bzip2", "xz",
        
        # Git operations
        "git",
        
        # Container operations
        "docker", "docker-compose", "podman", "buildah",
        
        # Network tunnels and VPNs
        "ssh", "scp", "rsync", "tailscale", "tailscaled", "cloudflared",
        
        # Package management (for troubleshooting)
        "apt", "apt-get", "dpkg", "snap", "yum", "dnf", "pacman",
        
        # System control (for service restart)
        "reboot", "shutdown", "halt", "poweroff", "init", "systemctl",
        
        # Monitoring and debugging
        "strace", "ltrace", "gdb", "valgrind", "perf", "iotop", "iostat",
        
        # Hardware and kernel
        "lshw", "lspci", "lsusb", "modprobe", "lsmod", "dmesg", "lspcmcia",
        
        # User and group management
        "useradd", "usermod", "userdel", "groupadd", "groupmod", "groupdel",
        "passwd", "chpasswd", "newusers", "vipw", "vigr",
        
        # Security and certificates
        "openssl", "certbot", "letsencrypt", "ufw", "iptables", "firewall-cmd",
        "ssh-keygen", "ssh-add", "ssh-copy-id",
        
        # Process and system monitoring
        "htop", "iotop", "iftop", "nethogs", "nload", "bmon", "nmtui",
        
        # File system operations
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
        "which", "whereis", "type", "hash", "alias", "unalias", "set", "env",
        "export", "unset", "readonly", "declare", "local", "return", "exit",
        "source", "exec", "eval", "trap", "wait", "jobs", "fg", "bg",
        "history", "fc", "pushd", "popd", "dirs", "cd", "pwd", "pushd",
        "popd", "dirs", "cd", "pwd", "pushd", "popd", "dirs", "cd", "pwd"
    ])
    
    denied_commands: List[str] = field(default_factory=lambda: [
        # Only block the most dangerous operations
        "rm -rf /",  # Prevent accidental root deletion
        "dd if=/dev/zero of=/dev/sda",  # Prevent disk wiping
        "mkfs.ext4 /dev/sda",  # Prevent filesystem destruction
        "fdisk /dev/sda",  # Prevent partition table destruction
    ])
    
    max_output_bytes: int = 10 * 1024 * 1024  # 10MB (for large logs, configs)
    max_output_lines: int = 10000  # For extensive logs
    command_timeout_seconds: int = 300  # 5 minutes for long operations
    rate_limit_per_minute: int = 500  # High rate for admin tasks
    max_sessions: int = 20  # Many concurrent sessions

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
        return cls(
            default_host=os.getenv('MCP_SSH_HOST'),
            default_port=int(os.getenv('MCP_SSH_PORT', '22')),
            default_username=os.getenv('MCP_SSH_USER'),
            key_path=os.getenv('MCP_SSH_KEY'),
            proxy_command=os.getenv('MCP_SSH_PROXY_COMMAND'),
            connect_timeout=int(os.getenv('MCP_SSH_CONNECT_TIMEOUT', '30')),
            keepalive_interval=int(os.getenv('MCP_SSH_KEEPALIVE', '30')),
            # Password configuration from environment
            default_password=os.getenv('MCP_SSH_PASSWORD'),
            sudo_password=os.getenv('MCP_SSH_SUDO_PASSWORD'),
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

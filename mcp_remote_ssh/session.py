"""SSH session management with persistent shell state."""

import asyncio
import threading
import time
import logging
import re
import base64
import os
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import paramiko
from paramiko import SSHClient, Channel, Transport
from .config import get_config
from .security import get_security_manager, CommandValidationResult

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Result of executing a command."""
    stdout: str
    stderr: str
    exit_status: Optional[int]
    duration_ms: int
    truncated: bool = False
    session_id: str = ""

@dataclass
class SessionInfo:
    """Information about an SSH session."""
    session_id: str
    host: str
    username: str
    connected_at: datetime
    last_used: datetime
    current_dir: str = "~"
    environment: Dict[str, str] = field(default_factory=dict)

class SSHSession:
    """Manages a persistent SSH session with shell state."""
    
    def __init__(self, session_id: str, host: str, port: int, username: str):
        self.session_id = session_id
        self.host = host
        self.port = port
        self.username = username
        self.client: Optional[SSHClient] = None
        self.channel: Optional[Channel] = None
        self.transport: Optional[Transport] = None
        self.connected = False
        self.lock = threading.Lock()
        self.last_used = datetime.now()
        self.current_dir = "~"
        self.environment: Dict[str, str] = {}
        self.prompt_pattern = re.compile(r'[\$#]\s*$', re.MULTILINE)
        self.config = get_config()
        self.security = get_security_manager()
        
    async def connect(self, auth_method: str = "key", **auth_kwargs) -> bool:
        """Establish SSH connection with persistent shell."""
        try:
            self.client = SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connection parameters
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': self.config.ssh.connect_timeout,
            }
            
            # Add ProxyCommand support if configured
            proxy_command = self.config.ssh.proxy_command
            if proxy_command:
                # Replace %h with hostname
                proxy_command = proxy_command.replace('%h', self.host)
                connect_kwargs['sock'] = paramiko.ProxyCommand(proxy_command)
            
            # Authentication
            if auth_method == "key":
                if 'key_path' in auth_kwargs:
                    connect_kwargs['key_filename'] = auth_kwargs['key_path']
                elif 'key_pem_base64' in auth_kwargs:
                    # Decode base64 key
                    key_data = base64.b64decode(auth_kwargs['key_pem_base64'])
                    # Create key object from string
                    from io import StringIO
                    key_file = StringIO(key_data.decode('utf-8'))
                    connect_kwargs['pkey'] = paramiko.RSAKey.from_private_key(key_file)
            elif auth_method == "password":
                connect_kwargs['password'] = auth_kwargs.get('password')
            
            # Connect
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.connect(**connect_kwargs)
            )
            
            # Get transport and open shell channel
            self.transport = self.client.get_transport()
            if not self.transport:
                raise Exception("Failed to get transport")
            
            self.channel = self.transport.open_session()
            if not self.channel:
                raise Exception("Failed to open channel")
            
            # Request PTY and shell
            self.channel.get_pty(term='xterm', width=120, height=30)
            self.channel.invoke_shell()
            
            # Wait for initial prompt and set up environment
            await self._wait_for_prompt()
            await self._setup_environment()
            
            self.connected = True
            logger.info(f"SSH session {self.session_id} connected to {self.username}@{self.host}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect SSH session {self.session_id}: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """Close SSH connection."""
        self.connected = False
        
        if self.channel:
            self.channel.close()
            self.channel = None
            
        if self.client:
            self.client.close()
            self.client = None
            
        if self.transport:
            self.transport.close()
            self.transport = None
            
        logger.info(f"SSH session {self.session_id} disconnected")
    
    async def execute_command(self, command: str, input_data: Optional[str] = None, 
                            timeout_ms: Optional[int] = None, 
                            max_bytes: Optional[int] = None) -> CommandResult:
        """Execute a command in the persistent shell."""
        if not self.connected or not self.channel:
            raise Exception("Session not connected")
        
        # Validate command
        validation = self.security.validate_command(command)
        if not validation.allowed:
            raise Exception(f"Command not allowed: {validation.reason}")
        
        start_time = time.time()
        timeout_seconds = (timeout_ms or self.config.security.command_timeout_seconds * 1000) / 1000
        max_output_bytes = max_bytes or self.config.security.max_output_bytes
        
        with self.lock:
            try:
                # Send command with exit status capture
                cmd_with_status = f"set +e; {validation.sanitized_cmd}; echo __EXIT_STATUS:$?__"
                
                self.channel.send(cmd_with_status + '\n')
                
                # Send input if provided
                if input_data:
                    self.channel.send(input_data)
                
                # Read output
                stdout_parts = []
                stderr_parts = []
                total_bytes = 0
                truncated = False
                exit_status = None
                
                # Read until we get the exit status marker or timeout
                end_time = time.time() + timeout_seconds
                buffer = ""
                
                while time.time() < end_time:
                    if self.channel.recv_ready():
                        chunk = self.channel.recv(4096).decode('utf-8', errors='ignore')
                        buffer += chunk
                        total_bytes += len(chunk)
                        
                        # Check for exit status marker
                        if '__EXIT_STATUS:' in buffer:
                            # Extract exit status
                            match = re.search(r'__EXIT_STATUS:(\d+)__', buffer)
                            if match:
                                exit_status = int(match.group(1))
                                # Remove the marker from output
                                buffer = re.sub(r'__EXIT_STATUS:\d+__\s*', '', buffer)
                                break
                        
                        # Check output limits
                        if total_bytes > max_output_bytes:
                            truncated = True
                            break
                    
                    if self.channel.recv_stderr_ready():
                        stderr_chunk = self.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
                        stderr_parts.append(stderr_chunk)
                        total_bytes += len(stderr_chunk)
                        
                        if total_bytes > max_output_bytes:
                            truncated = True
                            break
                    
                    # Small delay to avoid busy waiting
                    await asyncio.sleep(0.01)
                
                # Clean up the output (remove command echo and prompts)
                stdout = self._clean_output(buffer)
                stderr = ''.join(stderr_parts)
                
                # Update last used time
                self.last_used = datetime.now()
                
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Redact secrets from output
                stdout = self.security.redact_secrets(stdout)
                stderr = self.security.redact_secrets(stderr)
                
                # Limit output lines
                stdout_lines = stdout.split('\n')
                if len(stdout_lines) > self.config.security.max_output_lines:
                    stdout_lines = stdout_lines[:self.config.security.max_output_lines]
                    stdout_lines.append(f"... [output truncated after {self.config.security.max_output_lines} lines]")
                    stdout = '\n'.join(stdout_lines)
                    truncated = True
                
                result = CommandResult(
                    stdout=stdout,
                    stderr=stderr,
                    exit_status=exit_status,
                    duration_ms=duration_ms,
                    truncated=truncated,
                    session_id=self.session_id
                )
                
                # Log command execution (if safe to log)
                if self.security.should_log_command(command):
                    logger.info(f"Session {self.session_id} executed: {command} (exit: {exit_status}, {duration_ms}ms)")
                
                return result
                
            except Exception as e:
                logger.error(f"Command execution failed in session {self.session_id}: {e}")
                raise
    
    async def upload_file(self, remote_path: str, content: bytes, mode: str = "644") -> bool:
        """Upload file content to remote system."""
        if not self.connected or not self.client:
            raise Exception("Session not connected")
        
        # Validate path
        path_validation = self.security.validate_file_path(remote_path)
        if not path_validation.allowed:
            raise Exception(f"Upload path not allowed: {path_validation.reason}")
        
        try:
            sftp = self.client.open_sftp()
            
            # Write content to remote file
            with sftp.file(path_validation.sanitized_cmd, 'wb') as f:
                f.write(content)
            
            # Set file mode
            sftp.chmod(path_validation.sanitized_cmd, int(mode, 8))
            
            sftp.close()
            
            logger.info(f"Session {self.session_id} uploaded file: {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"File upload failed in session {self.session_id}: {e}")
            return False
    
    async def download_file(self, remote_path: str, max_bytes: Optional[int] = None) -> Optional[bytes]:
        """Download file content from remote system."""
        if not self.connected or not self.client:
            raise Exception("Session not connected")
        
        # Validate path
        path_validation = self.security.validate_file_path(remote_path)
        if not path_validation.allowed:
            raise Exception(f"Download path not allowed: {path_validation.reason}")
        
        max_size = max_bytes or self.config.security.max_output_bytes
        
        try:
            sftp = self.client.open_sftp()
            
            # Check file size
            file_stat = sftp.stat(path_validation.sanitized_cmd)
            if file_stat.st_size > max_size:
                raise Exception(f"File too large: {file_stat.st_size} bytes > {max_size} bytes")
            
            # Read file content
            with sftp.file(path_validation.sanitized_cmd, 'rb') as f:
                content = f.read(max_size)
            
            sftp.close()
            
            logger.info(f"Session {self.session_id} downloaded file: {remote_path}")
            return content
            
        except Exception as e:
            logger.error(f"File download failed in session {self.session_id}: {e}")
            return None
    
    async def _wait_for_prompt(self, timeout: float = 10.0):
        """Wait for shell prompt to appear."""
        end_time = time.time() + timeout
        buffer = ""
        
        while time.time() < end_time:
            if self.channel.recv_ready():
                chunk = self.channel.recv(1024).decode('utf-8', errors='ignore')
                buffer += chunk
                
                # Look for common prompt patterns
                if self.prompt_pattern.search(buffer):
                    return
                    
            await asyncio.sleep(0.1)
        
        logger.warning(f"Prompt not detected in session {self.session_id}")
    
    async def _setup_environment(self):
        """Set up shell environment for better interaction."""
        setup_commands = [
            "export TERM=xterm",
            "export PS1='$ '",  # Simple prompt
            "set +o emacs",     # Disable line editing
            "stty -echo",       # Disable echo for cleaner output
        ]
        
        for cmd in setup_commands:
            try:
                self.channel.send(cmd + '\n')
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Setup command failed: {cmd} - {e}")
    
    def _clean_output(self, output: str) -> str:
        """Clean command output by removing echoes and prompts."""
        lines = output.split('\n')
        
        # Remove empty lines and prompt lines
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not self.prompt_pattern.match(line):
                # Remove ANSI escape sequences
                line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def get_info(self) -> SessionInfo:
        """Get session information."""
        return SessionInfo(
            session_id=self.session_id,
            host=self.host,
            username=self.username,
            connected_at=datetime.now(),  # This should be stored when connecting
            last_used=self.last_used,
            current_dir=self.current_dir,
            environment=self.environment.copy()
        )

class SessionManager:
    """Manages multiple SSH sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, SSHSession] = {}
        self.config = get_config()
        self.lock = threading.Lock()
    
    async def create_session(self, session_id: str, host: str, port: int = 22, 
                           username: Optional[str] = None) -> SSHSession:
        """Create a new SSH session."""
        if len(self.sessions) >= self.config.security.max_sessions:
            # Remove oldest session
            await self._cleanup_oldest_session()
        
        username = username or self.config.ssh.default_username or "root"
        
        session = SSHSession(session_id, host, port, username)
        
        with self.lock:
            self.sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SSHSession]:
        """Get existing session by ID."""
        return self.sessions.get(session_id)
    
    async def remove_session(self, session_id: str):
        """Remove and disconnect session."""
        session = self.sessions.get(session_id)
        if session:
            await session.disconnect()
            with self.lock:
                del self.sessions[session_id]
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_used > timedelta(hours=8):  # 8 hour timeout
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.remove_session(session_id)
    
    async def _cleanup_oldest_session(self):
        """Remove the oldest session to make room for new one."""
        if not self.sessions:
            return
        
        oldest_session_id = min(self.sessions.keys(), 
                               key=lambda sid: self.sessions[sid].last_used)
        await self.remove_session(oldest_session_id)
    
    def list_sessions(self) -> List[SessionInfo]:
        """List all active sessions."""
        return [session.get_info() for session in self.sessions.values()]

# Global session manager
session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get the global session manager."""
    return session_manager

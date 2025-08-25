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
from .password_handler import create_password_manager
from .interactive_password_service import get_password_service

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
                            max_bytes: Optional[int] = None,
                            sudo_password: Optional[str] = None) -> CommandResult:
        """Execute a command in the persistent shell."""
        self._validate_session_state()
        self._validate_command(command)
        
        execution_context = self._create_execution_context(command, timeout_ms, max_bytes, sudo_password)
        
        with self.lock:
            try:
                self._send_command(execution_context)
                output_data = await self._read_command_output(execution_context)
                result = self._create_command_result(execution_context, output_data)
                self._log_command_execution(command, result)
                return result
                
            except Exception as e:
                logger.error(f"Command execution failed in session {self.session_id}: {e}")
                raise
    
    def _validate_session_state(self) -> None:
        """Validate that the session is connected and ready."""
        if not self.connected or not self.channel:
            raise Exception("Session not connected")
    
    def _validate_command(self, command: str) -> None:
        """Validate that the command is allowed to execute."""
        validation = self.security.validate_command(command)
        if not validation.allowed:
            raise Exception(f"Command not allowed: {validation.reason}")
    
    def _create_execution_context(self, command: str, timeout_ms: Optional[int], 
                                max_bytes: Optional[int], sudo_password: Optional[str]) -> Dict[str, Any]:
        """Create execution context with all necessary parameters."""
        # Create password manager with interactive support
        password_manager = None
        if sudo_password or self.config.ssh.enable_interactive_password:
            password_service = get_password_service()
            
            # Create interactive callback if enabled
            interactive_callback = None
            if self.config.ssh.enable_interactive_password:
                async def password_callback(prompt, context):
                    return await password_service.request_password(
                        prompt_text=prompt.prompt_text,
                        prompt_type=prompt.prompt_type,
                        session_id=self.session_id,
                        host=self.host,
                        username=self.username,
                        command=command
                    )
                interactive_callback = password_callback
            
            password_manager = create_password_manager(
                sudo_password=sudo_password,
                interactive_callback=interactive_callback,
                enable_interactive=self.config.ssh.enable_interactive_password
            )
        
        return {
            'command': command,
            'start_time': time.time(),
            'timeout_seconds': (timeout_ms or self.config.security.command_timeout_seconds * 1000) / 1000,
            'max_output_bytes': max_bytes or self.config.security.max_output_bytes,
            'password_manager': password_manager,
            'sanitized_command': self.security.validate_command(command).sanitized_cmd
        }
    
    def _send_command(self, context: Dict[str, Any]) -> None:
        """Send the command to the SSH channel."""
        cmd_with_status = f"set +e; {context['sanitized_command']}; echo __EXIT_STATUS:$?__"
        self.channel.send(cmd_with_status + '\n')
    
    async def _read_command_output(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Read command output with timeout and password handling."""
        output_data = {
            'stdout_parts': [],
            'stderr_parts': [],
            'buffer': "",
            'total_bytes': 0,
            'truncated': False,
            'exit_status': None
        }
        
        end_time = time.time() + context['timeout_seconds']
        last_output_time = time.time()
        
        while time.time() < end_time:
            if self._is_hanging(last_output_time, context['start_time']):
                return self._create_timeout_result(context['start_time'])
            
            await self._process_stdout_chunk(context, output_data, last_output_time)
            await self._process_stderr_chunk(context, output_data, last_output_time)
            
            if self._should_stop_reading(output_data, context):
                break
            
            await asyncio.sleep(0.01)
        
        return output_data
    
    def _is_hanging(self, last_output_time: float, start_time: float) -> bool:
        """Check if command is hanging (no output for 10 seconds)."""
        return time.time() - last_output_time > 10
    
    def _create_timeout_result(self, start_time: float) -> Dict[str, Any]:
        """Create timeout result when command is hanging."""
        logger.warning(f"Command appears to be hanging (no output for 10s) in session {self.session_id}")
        return {
            'stdout_parts': [],
            'stderr_parts': [],
            'buffer': "",
            'total_bytes': 0,
            'truncated': False,
            'exit_status': 1,
            'timeout_error': "Command timed out - may be waiting for input. Check if password is required."
        }
    
    async def _process_stdout_chunk(self, context: Dict[str, Any], output_data: Dict[str, Any], 
                                  last_output_time: float) -> None:
        """Process a chunk of stdout data."""
        if not self.channel.recv_ready():
            return
        
        chunk = self.channel.recv(4096).decode('utf-8', errors='ignore')
        output_data['buffer'] += chunk
        output_data['total_bytes'] += len(chunk)
        last_output_time = time.time()
        
        await self._handle_password_prompts(context, output_data)
        self._check_exit_status(output_data)
    
    async def _process_stderr_chunk(self, context: Dict[str, Any], output_data: Dict[str, Any], 
                                  last_output_time: float) -> None:
        """Process a chunk of stderr data."""
        if not self.channel.recv_stderr_ready():
            return
        
        stderr_chunk = self.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
        output_data['stderr_parts'].append(stderr_chunk)
        output_data['total_bytes'] += len(stderr_chunk)
        last_output_time = time.time()
    
    async def _handle_password_prompts(self, context: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """Handle password prompts in the output."""
        if context['password_manager']:
            await self._handle_password_with_manager(context, output_data)
        else:
            self._check_for_password_prompt_without_manager(context, output_data)
    
    async def _handle_password_with_manager(self, context: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """Handle password prompt using password manager."""
        prompt_context = {
            "session_id": self.session_id,
            "command": context['command'],
            "host": self.host,
            "username": self.username
        }
        
        password_response = await context['password_manager'].detect_and_handle_prompt(
            output_data['buffer'], prompt_context
        )
        
        if password_response and password_response.password:
            self.channel.send(password_response.password + '\n')
            logger.info(f"Sent password for session {self.session_id}")
            output_data['buffer'] = ""
        elif password_response and password_response.error:
            logger.warning(f"Password handling error: {password_response.error}")
    
    def _check_for_password_prompt_without_manager(self, context: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """Check for password prompt when no password manager is available."""
        sudo_patterns = [
            r'\[sudo\] password for [^:]+:',
            r'Password:',
            r'sudo: a terminal is required to read the password',
        ]
        
        for pattern in sudo_patterns:
            if re.search(pattern, output_data['buffer'], re.IGNORECASE):
                logger.warning(f"Password prompt detected but no password provided for session {self.session_id}")
                output_data['password_error'] = "Password required but not provided. Use sudo_password parameter."
                output_data['exit_status'] = 1
                break
    
    def _check_exit_status(self, output_data: Dict[str, Any]) -> None:
        """Check for exit status marker in output."""
        if '__EXIT_STATUS:' in output_data['buffer']:
            match = re.search(r'__EXIT_STATUS:(\d+)__', output_data['buffer'])
            if match:
                output_data['exit_status'] = int(match.group(1))
                output_data['buffer'] = re.sub(r'__EXIT_STATUS:\d+__\s*', '', output_data['buffer'])
    
    def _should_stop_reading(self, output_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Determine if we should stop reading output."""
        return (output_data['exit_status'] is not None or 
                output_data['total_bytes'] > context['max_output_bytes'] or
                'password_error' in output_data or
                'timeout_error' in output_data)
    
    def _create_command_result(self, context: Dict[str, Any], output_data: Dict[str, Any]) -> CommandResult:
        """Create CommandResult from execution context and output data."""
        if 'timeout_error' in output_data:
            return CommandResult(
                stdout="",
                stderr=output_data['timeout_error'],
                exit_status=1,
                duration_ms=int((time.time() - context['start_time']) * 1000),
                truncated=False,
                session_id=self.session_id
            )
        
        if 'password_error' in output_data:
            return CommandResult(
                stdout="",
                stderr=output_data['password_error'],
                exit_status=1,
                duration_ms=int((time.time() - context['start_time']) * 1000),
                truncated=False,
                session_id=self.session_id
            )
        
        stdout = self._clean_output(output_data['buffer'])
        stderr = ''.join(output_data['stderr_parts'])
        
        # Update last used time
        self.last_used = datetime.now()
        
        # Calculate duration
        duration_ms = int((time.time() - context['start_time']) * 1000)
        
        # Redact secrets from output
        stdout = self.security.redact_secrets(stdout)
        stderr = self.security.redact_secrets(stderr)
        
        # Limit output lines
        stdout, truncated = self._limit_output_lines(stdout, output_data['truncated'])
        
        return CommandResult(
            stdout=stdout,
            stderr=stderr,
            exit_status=output_data['exit_status'],
            duration_ms=duration_ms,
            truncated=truncated,
            session_id=self.session_id
        )
    
    def _limit_output_lines(self, stdout: str, already_truncated: bool) -> Tuple[str, bool]:
        """Limit stdout to maximum number of lines."""
        stdout_lines = stdout.split('\n')
        truncated = already_truncated
        
        if len(stdout_lines) > self.config.security.max_output_lines:
            stdout_lines = stdout_lines[:self.config.security.max_output_lines]
            stdout_lines.append(f"... [output truncated after {self.config.security.max_output_lines} lines]")
            stdout = '\n'.join(stdout_lines)
            truncated = True
        
        return stdout, truncated
    
    def _log_command_execution(self, command: str, result: CommandResult) -> None:
        """Log command execution if safe to do so."""
        if self.security.should_log_command(command):
            logger.info(f"Session {self.session_id} executed: {command} (exit: {result.exit_status}, {result.duration_ms}ms)")
    
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
    
    def get_session_info(self) -> SessionInfo:
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

# Session manager is now in session_manager.py

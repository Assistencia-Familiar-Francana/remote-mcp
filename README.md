# MCP Remote SSH Server

A secure Model Context Protocol (MCP) server that provides controlled SSH access to remote machines through Claude Desktop, Cursor, or other MCP-compatible clients.

## 🚀 Features

- **Persistent SSH Sessions**: Maintains shell state across commands (cwd, environment)
- **Security First**: Command allowlist, output limits, timeout controls
- **Multiple Sessions**: Manage multiple SSH connections simultaneously  
- **File Operations**: Upload/download files with safety checks
- **Cloudflare Tunnel Support**: Works with your existing tunnel setup
- **Comprehensive Logging**: Safe logging with secret redaction

## 🔧 Installation

### Using uv (Recommended)
```bash
git clone <your-repo>
cd remote-mcp
uv sync
```

### Using pip
```bash
git clone <your-repo>
cd remote-mcp
pip install -e .
```

## ⚙️ Configuration

### Environment Variables
```bash
# Copy example configuration
cp env.example .env

# Edit configuration
MCP_SSH_HOST=your-remote-host.com
MCP_SSH_PORT=22
MCP_SSH_USER=your-username
MCP_SSH_KEY=/path/to/your/private/key
DEBUG=false
```

### For Your Cloudflare Setup
```bash
# For ff node (direct access)
MCP_SSH_HOST=100.65.56.110
MCP_SSH_USER=abel
MCP_SSH_PORT=22

# For bourbaki node (via tunnel)
# First start tunnel: cloudflared access tcp --hostname bourbaki.buddhilw.com --listener 127.0.0.1:2222
MCP_SSH_HOST=127.0.0.1
MCP_SSH_PORT=2222
MCP_SSH_USER=euler
```

### Advanced Configuration
Create `mcp_ssh_config.yaml` to customize security settings:

```yaml
security:
  allowed_commands:
    - "kubectl"
    - "docker"
    - "systemctl"
    # ... more commands
  
  max_output_bytes: 131072  # 128KB
  command_timeout_seconds: 30
  max_sessions: 5
```

## 🚦 Quick Start

### 1. Start the MCP Server
```bash
# Using uv
uv run python -m mcp_remote_ssh.server

# Using python directly  
python -m mcp_remote_ssh.server
```

### 2. Configure Cursor/Claude Desktop

Add to your MCP configuration file:

**Cursor**: `~/.cursor/mcp.json`
**Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "remote-ssh": {
      "command": "python",
      "args": ["-m", "mcp_remote_ssh.server"],
      "env": {
        "MCP_SSH_HOST": "100.65.56.110",
        "MCP_SSH_USER": "abel",
        "MCP_SSH_KEY": "/home/ramanujan/.ssh/id_ed25519"
      }
    }
  }
}
```

### 3. Use in Claude/Cursor

```
Connect to my Kubernetes master node and check the pod status.
```

The AI will automatically:
1. Establish SSH connection using `ssh_connect`
2. Execute `kubectl get pods` using `ssh_run`
3. Return formatted results

## 🛠️ Available Tools

### `ssh_connect`
Establish SSH connection to remote host.
```python
ssh_connect(
    host="100.65.56.110",
    port=22,
    username="abel",
    auth={"key_path": "/path/to/key"}
)
```

### `ssh_run`
Execute command in persistent session.
```python
ssh_run(
    session_id="abc123",
    cmd="kubectl get pods -n funeraria-francana",
    timeout_ms=30000
)
```

### `ssh_upload`
Upload file to remote system.
```python
ssh_upload(
    session_id="abc123", 
    path="/tmp/config.yaml",
    bytes_base64="<base64-encoded-content>"
)
```

### `ssh_download`
Download file from remote system.
```python
ssh_download(
    session_id="abc123",
    path="/var/log/app.log",
    max_bytes=65536
)
```

### `ssh_list_sessions`
List all active SSH sessions.

### `ssh_disconnect`
Close SSH session.

## 🔒 Security Features

### Command Allowlist
Only pre-approved commands can be executed:
- File operations: `ls`, `cat`, `head`, `tail`, `grep`, `find`
- System info: `uname`, `whoami`, `uptime`, `free`
- Kubernetes: `kubectl`, `helm`
- Docker: `docker`, `docker-compose`
- System services: `systemctl status`, `journalctl`

### Prohibited Commands
Dangerous operations are blocked:
- File modification: `rm`, `mv`, `cp`
- System changes: `sudo`, `passwd`, `reboot`
- Network tools: `nc`, `telnet`, `ssh`

### Output Protection
- Maximum output size (128KB default)
- Line count limits (1000 lines default)  
- Command timeouts (30 seconds default)
- Secret redaction (API keys, tokens, private keys)

### Path Validation
File operations restricted to safe directories:
- `/home/` - User directories
- `/var/log/` - Log files
- `/tmp/` - Temporary files
- `/opt/` - Optional software

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mcp_remote_ssh

# Run specific test file
uv run pytest mcp_remote_ssh/tests/test_security.py -v
```

### Integration Tests
```bash
# Requires Docker for SSH server
docker run -d -p 2222:22 linuxserver/openssh-server
uv run pytest -m integration
```

## 🐛 Debugging

### Enable Debug Mode
```bash
DEBUG=true python -m mcp_remote_ssh.server
```

### Check Logs
```bash
# Server logs show connection attempts and command execution
tail -f ~/.local/share/mcp-remote-ssh/logs/server.log
```

### Validate Commands
```python
# Test command validation
ssh_validate_command("kubectl get pods")
# Returns: {"allowed": true, "reason": "Command allowed"}
```

## 🚨 Security Considerations

### Recommended Setup
1. **Dedicated User**: Create restricted user for MCP access
   ```bash
   sudo useradd -m -s /bin/bash mcp-user
   sudo usermod -aG docker mcp-user  # If needed
   ```

2. **SSH Key Authentication**: Never use passwords
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/mcp_key
   ssh-copy-id -i ~/.ssh/mcp_key mcp-user@remote-host
   ```

3. **Network Restrictions**: Use firewall rules or VPN
   ```bash
   # Limit SSH access to specific IPs
   sudo ufw allow from YOUR.IP.ADDRESS to any port 22
   ```

### Production Checklist
- [ ] Dedicated user account with minimal privileges
- [ ] SSH key authentication only (no passwords)
- [ ] Firewall rules restricting SSH access
- [ ] Regular security updates on remote systems
- [ ] Monitor logs for suspicious activity
- [ ] Test command allowlist thoroughly
- [ ] Set appropriate resource limits

## 🎯 Use Cases

### Kubernetes Management
```
Check the status of my funeral announcement backend pods and show recent logs.
```

### System Monitoring
```
Show me the system resources and check if any services are failing.
```

### Log Analysis
```
Search the nginx logs for any 5xx errors in the last hour.
```

### File Management
```
Download the latest application config file and show me its contents.
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`uv run pytest`)
5. Submit pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [Model Context Protocol](https://docs.anthropic.com/en/docs/mcp)
- [Paramiko Documentation](https://docs.paramiko.org/)
- [FastMCP](https://github.com/jlowin/fastmcp)

---

**⚠️ Important**: This tool provides AI agents with shell access to your systems. Always review the security settings and use dedicated accounts with minimal privileges.
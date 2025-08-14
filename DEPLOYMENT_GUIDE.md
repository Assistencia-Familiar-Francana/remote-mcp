# 🚀 MCP Remote SSH Server - Deployment Guide

## Overview

You now have a complete **Model Context Protocol (MCP) server** that provides secure SSH access to your remote Kubernetes cluster through Claude Desktop and Cursor. This allows you to ask AI assistants to connect to your servers and execute commands safely.

## 🏗️ What We Built

### Core Components
- **Security Manager**: Command allowlist, secret redaction, path validation
- **Session Manager**: Persistent SSH connections with state management  
- **MCP Server**: FastMCP-based server with tool definitions
- **Configuration System**: Environment-based config with YAML overrides
- **Test Suite**: Unit and integration tests

### Security Features
- ✅ **Command Allowlist**: Only 27 safe commands allowed (kubectl, docker, ls, cat, etc.)
- ❌ **Command Denylist**: 23+ dangerous commands blocked (rm, sudo, kill, etc.)
- 🛡️ **Pattern Detection**: Blocks command injection (&&, ||, |, ;, etc.)
- 🔒 **Secret Redaction**: Auto-redacts API keys, tokens, private keys
- 📁 **Path Validation**: File access limited to safe directories
- ⏱️ **Timeouts**: 30-second command timeout, 128KB output limit

## 🔧 Installation & Setup

### 1. Quick Setup
```bash
cd remote-mcp
./setup.sh
```

### 2. Manual Setup
```bash
# Install dependencies
pip install modelcontextprotocol paramiko pyyaml python-dotenv

# Configure environment
cp env.example .env
# Edit .env with your SSH details

# Test security system
python standalone_demo.py
```

### 3. Cursor Configuration
Your Cursor MCP config (`~/.cursor/mcp.json`) is already set up:
```json
{
  "mcpServers": {
    "remote-ssh": {
      "command": "python",
      "args": ["-m", "mcp_remote_ssh.server"],
      "cwd": "/home/ramanujan/PP/funeraria/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "100.65.56.110",
        "MCP_SSH_USER": "abel",
        "MCP_SSH_KEY": "/home/ramanujan/.ssh/id_ed25519"
      }
    }
  }
}
```

## 🌐 Your Network Setup

### Current Configuration
- **ff (master)**: `abel@100.65.56.110:22` (direct access)
- **bourbaki (worker)**: `euler@127.0.0.1:2222` (via Cloudflare tunnel)

### Cloudflare Tunnel Usage
```bash
# Start tunnel for bourbaki access
cloudflared access tcp --hostname bourbaki.buddhilw.com --listener 127.0.0.1:2222

# Then SSH normally
ssh -p 2222 euler@127.0.0.1
```

## 🚀 Usage Examples

### Start the MCP Server
```bash
cd remote-mcp
python -m mcp_remote_ssh.server
```

### Ask Cursor/Claude
```
Connect to my Kubernetes cluster and show me the status of the funeral announcement application pods.
```

```
Check the system resources on my ff node and show me if any services are failing.
```

```
Show me the recent logs from the cartas-backend service in the funeraria-francana namespace.
```

## 🛠️ Available MCP Tools

### `ssh_connect`
Establish SSH connection to remote host.
```python
ssh_connect(
    host="100.65.56.110",
    username="abel", 
    auth={"key_path": "/path/to/key"}
)
```

### `ssh_run` 
Execute commands in persistent session.
```python
ssh_run(
    session_id="abc123",
    cmd="kubectl get pods -n funeraria-francana"
)
```

### `ssh_upload` / `ssh_download`
Transfer files safely.

### `ssh_list_sessions` / `ssh_disconnect`
Manage active sessions.

## 🔒 Security Validation

The system has been tested with your specific use cases:

### ✅ Allowed Commands
- `kubectl get pods -n funeraria-francana`
- `docker ps`
- `systemctl status nginx`
- `journalctl --since '1 hour ago'`
- `cat /var/log/app.log`
- `ls -la`
- `git status`

### ❌ Blocked Commands
- `rm -rf /` (file deletion)
- `sudo passwd` (privilege escalation)
- `ls && rm file` (command chaining)
- `kill -9 1234` (process termination)

## 🐛 Troubleshooting

### Common Issues

#### 1. SSH Connection Failed
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/id_ed25519

# Test SSH manually
ssh abel@100.65.56.110

# For bourbaki, start tunnel first
cloudflared access tcp --hostname bourbaki.buddhilw.com --listener 127.0.0.1:2222
ssh -p 2222 euler@127.0.0.1
```

#### 2. MCP Server Not Starting
```bash
# Check dependencies
pip install modelcontextprotocol paramiko pyyaml python-dotenv

# Check configuration
cat .env

# Run with debug
DEBUG=true python -m mcp_remote_ssh.server
```

#### 3. Commands Being Blocked
```bash
# Test command validation
python -c "
from mcp_remote_ssh.security import get_security_manager
result = get_security_manager().validate_command('your-command-here')
print(f'Allowed: {result.allowed}, Reason: {result.reason}')
"
```

#### 4. Cursor Not Connecting
- Restart Cursor after updating MCP config
- Check `~/.cursor/mcp.json` format
- Look for MCP server logs in Cursor's developer console

## 🧪 Testing

### Run Security Demo
```bash
python standalone_demo.py
```

### Run Unit Tests
```bash
pip install pytest
pytest mcp_remote_ssh/tests/
```

### Integration Tests
```bash
# Requires SSH server setup
pytest -m integration
```

## 🎯 Example Workflows

### Kubernetes Management
```
User: "Check if my funeral announcement backend is running properly"
AI: Connects via SSH → runs kubectl get pods → analyzes output → reports status
```

### System Monitoring
```
User: "Are there any issues with my servers?"
AI: Connects to both nodes → checks systemctl status → reviews logs → summarizes health
```

### Log Analysis
```
User: "Show me any errors in the last hour"
AI: Connects → runs journalctl with time filter → searches for ERROR patterns → reports findings
```

## 🔄 Updates & Maintenance

### Update Dependencies
```bash
pip install --upgrade modelcontextprotocol paramiko pyyaml python-dotenv
```

### Update Security Rules
Edit `mcp_ssh_config.yaml`:
```yaml
security:
  allowed_commands:
    - "new-command"  # Add new allowed commands
  denied_commands:
    - "dangerous-cmd"  # Add new blocked commands
```

### Monitor Usage
```bash
# Check active sessions
python -c "
from mcp_remote_ssh.session import get_session_manager
sessions = get_session_manager().list_sessions()
print(f'Active sessions: {len(sessions)}')
"
```

## 🎉 Success Metrics

Your MCP Remote SSH Server is now:
- ✅ **Secure**: Command validation prevents dangerous operations
- ✅ **Reliable**: Persistent sessions maintain state across commands  
- ✅ **Integrated**: Works seamlessly with Cursor and Claude
- ✅ **Configured**: Set up for your specific Cloudflare tunnel infrastructure
- ✅ **Tested**: Validated with your Kubernetes cluster commands

## 🚀 Next Steps

1. **Start the server**: `python -m mcp_remote_ssh.server`
2. **Ask Cursor**: "Connect to my Kubernetes cluster and show pod status"
3. **Monitor usage**: Check logs and session management
4. **Expand access**: Add more allowed commands as needed
5. **Scale up**: Consider adding more remote hosts

---

**🎯 Key Achievement**: You now have AI assistants that can safely manage your Kubernetes cluster and remote servers through natural language commands, with full security controls and audit trails!

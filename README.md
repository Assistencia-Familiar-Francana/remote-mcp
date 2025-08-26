# MCP Remote SSH Server

A robust, SOLID-compliant Multi-Context Protocol (MCP) server for remote SSH operations with advanced password management and security features.

## 🚀 Features

- **SOLID Architecture**: Clean, maintainable code following SOLID principles
- **Advanced Password Management**: Environmental, interactive, and session-specific password handling
- **Security-First**: Comprehensive security patterns and command validation
- **Session Management**: Persistent SSH sessions with automatic cleanup
- **Tool Handlers**: Extensible tool system for SSH operations
- **Timeout Management**: Intelligent timeout handling to prevent hanging commands
- **🔒 Permissibility Levels**: Configurable security levels (low, medium, high) for fine-grained access control

## 🔒 Permissibility Levels

The MCP Remote SSH server supports three configurable permissibility levels that control which commands and operations are allowed:

### **Low Permissibility** (Read-Only Operations)
- **Description**: Basic read-only operations only
- **Allowed**: File viewing, system information, network diagnostics
- **Blocked**: File modifications, sudo, command chaining, system changes
- **Use Case**: Monitoring, diagnostics, read-only access

**Example Commands**:
```bash
ls -la                    # ✅ Allowed
cat /etc/hostname        # ✅ Allowed
ps aux                   # ✅ Allowed
df -h                    # ✅ Allowed
sudo apt update          # ❌ Denied
cp file1 file2           # ❌ Denied
ls && echo 'success'     # ❌ Denied
```

### **Medium Permissibility** (Safe Operations)
- **Description**: Read operations + safe write operations
- **Allowed**: File operations, system administration (non-destructive), package management
- **Blocked**: Sudo operations, dangerous system modifications, command chaining
- **Use Case**: Development, testing, safe administrative tasks

**Example Commands**:
```bash
ls -la                    # ✅ Allowed
cp file1 file2           # ✅ Allowed
systemctl status ssh     # ✅ Allowed
journalctl -u ssh        # ✅ Allowed
sudo apt update          # ❌ Denied
sudo reboot              # ❌ Denied
ls && echo 'success'     # ❌ Denied
```

### **High Permissibility** (Administrative Access)
- **Description**: Full administrative access with sudo
- **Allowed**: All operations including sudo, command chaining, system control
- **Blocked**: Only the most dangerous operations (rm -rf /, disk wiping, etc.)
- **Use Case**: System administration, deployment, full access scenarios

**Example Commands**:
```bash
ls -la                    # ✅ Allowed
sudo apt update          # ✅ Allowed
sudo systemctl restart ssh # ✅ Allowed
ls && echo 'success'     # ✅ Allowed
ps aux | grep ssh        # ✅ Allowed
rm -rf /                 # ❌ Denied (always blocked)
dd if=/dev/zero of=/dev/sda # ❌ Denied (always blocked)
```

### Configuration

#### Environment Variable
```bash
export MCP_SSH_PERMISSIBILITY_LEVEL=high
```

#### JSON Configuration File
```yaml
security:
  permissibility_level: high  # low, medium, or high
```

#### MCP Configuration
```json
{
  "mcpServers": {
    "production-ssh": {
      "env": {
        "MCP_SSH_PERMISSIBILITY_LEVEL": "high"
      }
    }
  }
}
```

### Getting Permissibility Information

Use the `ssh_get_permissibility_info` tool to check current settings:

```python
# This will return information about the current permissibility level
# and what operations are allowed/blocked
```

## 📁 Project Structure

```
remote-mcp/
├── mcp_remote_ssh/          # Main package
│   ├── __init__.py
│   ├── server.py            # MCP server implementation
│   ├── session.py           # SSH session management
│   ├── session_manager.py   # Session lifecycle management
│   ├── tool_handlers.py     # Tool handler implementations
│   ├── config.py            # Configuration management
│   ├── security.py          # Security validation
│   ├── security_patterns.py # Security pattern management
│   ├── password_handler.py  # Password handling system
│   ├── interactive_password_service.py # Interactive password service
│   └── tests/               # Unit and integration tests
├── docs/                    # Documentation
├── demos/                   # Example demonstrations
├── scripts/                 # Utility scripts
├── configs/                 # Configuration files
├── start_mcp_server.py      # Server startup script
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## 🛠️ Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd remote-mcp

# Install dependencies
pip install -r requirements.txt
```

### Configuration

#### Environment Variables

Set up environment variables:

```bash
export MCP_SSH_HOST="your-host.com"
export MCP_SSH_USER="your-username"
export MCP_SSH_KEY="/path/to/your/ssh/key"
export MCP_SSH_SUDO_PASSWORD="your-sudo-password"  # Optional
export MCP_SSH_INTERACTIVE_PASSWORD="true"         # Optional

# Password Configuration
export MCP_PASSWORD="your-default-password"        # Fallback for both SSH and sudo
export MCP_SSH_PASSWORD="your-ssh-password"        # SSH-specific password
export MCP_SSH_SUDO_PASSWORD="your-sudo-password"  # Sudo-specific password
```

**Password Priority Order:**
1. `MCP_SSH_PASSWORD` / `MCP_SSH_SUDO_PASSWORD` (specific passwords)
2. `MCP_PASSWORD` (fallback for both)
3. No password (interactive prompt if enabled)

#### MCP Configuration File

For Cursor IDE integration, create a `.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "production-ssh": {
      "command": "/usr/bin/python3",
      "args": ["/path/to/remote-mcp/start_mcp_server.py"],
      "cwd": "/path/to/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "your-production-host.com",
        "MCP_SSH_USER": "admin",
        "MCP_SSH_KEY": "/path/to/your/ssh/private_key",
        "MCP_SSH_PORT": "22",
        "MCP_SSH_PROXY_COMMAND": "cloudflared access ssh --hostname %h",
        "MCP_SERVER_NAME": "production-ssh",
        "MCP_SERVER_DESCRIPTION": "Production Server - Enhanced Permissions for Admin",
        "MCP_SSH_SUDO_PASSWORD": "your-sudo-password",
        "MCP_SSH_INTERACTIVE_PASSWORD": "true",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO"
      }
    },
    "staging-ssh": {
      "command": "/usr/bin/python3",
      "args": ["/path/to/remote-mcp/start_mcp_server.py"],
      "cwd": "/path/to/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "staging.example.com",
        "MCP_SSH_USER": "deploy",
        "MCP_SSH_KEY": "/path/to/your/ssh/staging_key",
        "MCP_SSH_PORT": "2222",
        "MCP_SERVER_NAME": "staging-ssh",
        "MCP_SERVER_DESCRIPTION": "Staging Server - Safe Operations Only",
        "MCP_SSH_PERMISSIBILITY_LEVEL": "medium",
        "MCP_PASSWORD": "your-default-password",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**Security Note**: Replace sensitive values like passwords, hostnames, and file paths with your actual configuration. Never commit real credentials to version control.

### Running the Server

```bash
python start_mcp_server.py
```

## 📚 Documentation

- **[Password Management](docs/PASSWORD_MANAGEMENT.md)** - Comprehensive guide to password handling
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Deployment and configuration instructions
- **[API Reference](docs/README.md)** - Detailed API documentation

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest mcp_remote_ssh/tests/

# Run specific test categories
python -m pytest mcp_remote_ssh/tests/test_tool_handlers.py
python -m pytest mcp_remote_ssh/tests/test_password_functionality.py
```

## 🔧 Development

### Architecture Overview

The project follows SOLID principles with clear separation of concerns:

- **Tool Handlers**: Each MCP tool has its own handler class
- **Session Management**: Centralized session lifecycle management
- **Security Patterns**: Extensible security pattern system
- **Password Management**: Multi-strategy password handling

### Adding New Tools

1. Create a new handler class in `tool_handlers.py`
2. Implement the `ToolHandler` interface
3. Add the handler to `ToolHandlerFactory`
4. Register the tool in `server.py`
5. Add tests in `tests/`

### Adding New Security Patterns

1. Create a new pattern class in `security_patterns.py`
2. Implement the `SecurityPattern` interface
3. Add the pattern to `SecurityPatternManager`
4. Add tests for the new pattern

## 🔒 Security

- **Command Validation**: All commands are validated against security patterns
- **Password Security**: Secure password handling with timeouts
- **Session Isolation**: Each session is isolated and managed separately
- **Audit Logging**: Comprehensive logging for security auditing

## 🤝 Contributing

1. Follow SOLID principles
2. Write comprehensive tests
3. Update documentation
4. Use meaningful commit messages

## 📄 License

[GNU General Public License (GPL) v3, 29 June 2007](./LICENSE)

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review the test examples in `mcp_remote_ssh/tests/`
3. Check the demo scripts in `demos/`

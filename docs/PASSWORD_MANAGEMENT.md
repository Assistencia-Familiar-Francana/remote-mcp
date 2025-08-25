# Password Management for MCP SSH Server

This document describes the password management features in the MCP SSH server, including environmental password configuration and interactive password prompting.

## Overview

The MCP SSH server now supports multiple password management strategies:

1. **Environmental Passwords** - Passwords stored in environment variables
2. **Interactive Passwords** - User prompts for passwords when needed
3. **Session-specific Passwords** - Passwords passed as parameters to specific commands

## Configuration

### Environment Variables

You can configure passwords using environment variables:

```bash
# SSH connection password
export MCP_SSH_PASSWORD="your_ssh_password"

# Sudo password for administrative commands
export MCP_SSH_SUDO_PASSWORD="your_sudo_password"

# Enable/disable interactive password prompts
export MCP_SSH_INTERACTIVE_PASSWORD="true"
```

### Configuration File

You can also set these in your `mcp_ssh_config.yaml`:

```yaml
ssh:
  default_password: "your_ssh_password"
  sudo_password: "your_sudo_password"
  enable_interactive_password: true
```

## Usage Patterns

### 1. Environmental Password (Recommended for Automation)

Set the `MCP_SSH_SUDO_PASSWORD` environment variable:

```bash
export MCP_SSH_SUDO_PASSWORD="your_sudo_password"
```

Then run commands normally - the password will be automatically used:

```bash
# The sudo password will be automatically provided
curl -X POST http://localhost:3000/ssh_run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "cmd": "sudo systemctl status k3s"}'
```

### 2. Interactive Password (Recommended for Manual Use)

Enable interactive passwords and use the password management tools:

```bash
# Enable interactive passwords
export MCP_SSH_INTERACTIVE_PASSWORD="true"

# Run a command that requires sudo
curl -X POST http://localhost:3000/ssh_run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "cmd": "sudo systemctl status k3s"}'
```

The command will pause and wait for a password. Check for pending requests:

```bash
# List pending password requests
curl -X POST http://localhost:3000/ssh_list_password_requests
```

Provide the password:

```bash
# Provide password for the request
curl -X POST http://localhost:3000/ssh_provide_password \
  -H "Content-Type: application/json" \
  -d '{"request_id": "request_uuid", "password": "your_password"}'
```

### 3. Session-specific Password

Pass the password directly with the command:

```bash
curl -X POST http://localhost:3000/ssh_run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123", 
    "cmd": "sudo systemctl status k3s",
    "sudo_password": "your_sudo_password"
  }'
```

## MCP Tools

### New Password Management Tools

The following new tools are available for password management:

#### `ssh_list_password_requests`

Lists all pending password requests.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "requests": [
    {
      "request_id": "uuid",
      "prompt_text": "[sudo] password for user:",
      "prompt_type": "sudo",
      "session_id": "abc123",
      "host": "host.com",
      "username": "user",
      "command": "sudo systemctl status k3s",
      "timestamp": "2024-01-15T10:30:00Z",
      "timeout_seconds": 60
    }
  ],
  "count": 1
}
```

#### `ssh_provide_password`

Provides a password for a pending request.

**Parameters:**
- `request_id` (string): The request ID from `ssh_list_password_requests`
- `password` (string): The password to provide

**Response:**
```json
{
  "success": true,
  "request_id": "uuid",
  "message": "Password provided for request uuid"
}
```

#### `ssh_cancel_password_request`

Cancels a pending password request.

**Parameters:**
- `request_id` (string): The request ID to cancel

**Response:**
```json
{
  "success": true,
  "request_id": "uuid",
  "message": "Password request uuid cancelled"
}
```

## Security Considerations

### Password Storage

1. **Environment Variables**: Passwords in environment variables are stored in memory and may be visible in process lists
2. **Configuration Files**: Passwords in YAML files should be properly secured with file permissions
3. **Interactive Mode**: Passwords are only stored temporarily in memory during the request

### Best Practices

1. **Use SSH Keys**: Prefer SSH key authentication over passwords when possible
2. **Limit Password Scope**: Use session-specific passwords for sensitive operations
3. **Timeout Management**: Password requests automatically timeout after 60 seconds
4. **Audit Logging**: All password operations are logged for security auditing

## Implementation Details

### Password Handler Architecture

The password management system follows SOLID principles:

- **`PasswordHandler`** (Interface): Defines the contract for password handlers
- **`SudoPasswordHandler`**: Handles sudo password prompts with pre-configured passwords
- **`InteractivePasswordHandler`**: Handles interactive password prompts via callbacks
- **`PasswordManager`**: Orchestrates multiple password handlers

### Interactive Password Service

The `InteractivePasswordService` manages password requests:

- **Request Tracking**: Maintains a registry of pending password requests
- **Timeout Management**: Automatically expires requests after timeout
- **Callback System**: Supports custom password request callbacks
- **Cleanup**: Background task cleans up expired requests

### Configuration Integration

Password configuration is integrated into the existing config system:

- **Environment Variables**: Loaded via `SSHConfig.from_env()`
- **YAML Files**: Supported in configuration files
- **Runtime Override**: Can be overridden per command

## Examples

### Example 1: Automated Kubernetes Administration

```bash
# Set up environment
export MCP_SSH_SUDO_PASSWORD="k8s_admin_password"
export MCP_SSH_HOST="k8s-master.example.com"
export MCP_SSH_USER="admin"

# Connect and run administrative commands
curl -X POST http://localhost:3000/ssh_connect \
  -H "Content-Type: application/json" \
  -d '{"host": "k8s-master.example.com", "username": "admin"}'

# The sudo password will be automatically used
curl -X POST http://localhost:3000/ssh_run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_id", "cmd": "sudo kubectl get nodes"}'
```

### Example 2: Interactive System Administration

```bash
# Enable interactive mode
export MCP_SSH_INTERACTIVE_PASSWORD="true"

# Run command that requires password
curl -X POST http://localhost:3000/ssh_run \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_id", "cmd": "sudo systemctl restart k3s"}'

# Check for password requests
curl -X POST http://localhost:3000/ssh_list_password_requests

# Provide password when prompted
curl -X POST http://localhost:3000/ssh_provide_password \
  -H "Content-Type: application/json" \
  -d '{"request_id": "request_id", "password": "your_password"}'
```

### Example 3: Mixed Mode (Environmental + Interactive)

```bash
# Set default sudo password
export MCP_SSH_SUDO_PASSWORD="default_sudo_password"

# Enable interactive for other prompts
export MCP_SSH_INTERACTIVE_PASSWORD="true"

# Commands will use environmental password for sudo
# But prompt for other password types (SSH, etc.)
```

## Troubleshooting

### Common Issues

1. **Password Not Provided**: Check if `MCP_SSH_SUDO_PASSWORD` is set or interactive mode is enabled
2. **Request Timeout**: Password requests timeout after 60 seconds
3. **Multiple Requests**: Use `ssh_list_password_requests` to see all pending requests
4. **Wrong Password**: Use `ssh_cancel_password_request` to cancel and retry

### Debug Mode

Enable debug logging to see password handling details:

```bash
export DEBUG="true"
export LOG_LEVEL="DEBUG"
```

### Testing

Use the test script to verify password functionality:

```bash
python test_password_functionality.py
```

## Migration Guide

### From Previous Version

If you were using the old password system:

1. **Update Environment Variables**: Add `MCP_SSH_SUDO_PASSWORD` for sudo passwords
2. **Enable Interactive Mode**: Set `MCP_SSH_INTERACTIVE_PASSWORD="true"` for interactive prompts
3. **Update Commands**: Remove manual password handling from your scripts
4. **Test**: Use the new password management tools to verify functionality

### Backward Compatibility

The new system maintains backward compatibility:
- Existing commands without password parameters continue to work
- The `sudo_password` parameter in `ssh_run` still works
- All existing MCP tools continue to function

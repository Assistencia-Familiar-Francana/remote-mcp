# Sudo Usage Guide for MCP Remote SSH

## Overview

This guide explains how to use sudo commands with the MCP Remote SSH server. The system now properly handles sudo password prompts and automatically passes the password when configured correctly.

## 🔧 Configuration

### 1. Set High Permissibility Level

First, you need to set the permissibility level to "high" to allow sudo commands:

#### Environment Variable
```bash
export MCP_SSH_PERMISSIBILITY_LEVEL=high
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

#### YAML Configuration File
```yaml
security:
  permissibility_level: high
```

### 2. Set Sudo Password

You need to provide the sudo password so the system can automatically respond to password prompts:

#### Environment Variable
```bash
export MCP_SSH_SUDO_PASSWORD=your_sudo_password
```

#### MCP_PASSWORD Fallback
You can also use `MCP_PASSWORD` as a fallback for both SSH and sudo passwords:
```bash
export MCP_PASSWORD=your_default_password
```

#### MCP Configuration
```json
{
  "mcpServers": {
    "production-ssh": {
      "env": {
        "MCP_SSH_PERMISSIBILITY_LEVEL": "high",
        "MCP_SSH_SUDO_PASSWORD": "your_sudo_password"
      }
    }
  }
}
```

#### YAML Configuration File
```yaml
ssh:
  sudo_password: your_sudo_password
```

## 🚀 Usage Examples

### Basic Sudo Commands

Once configured, you can use sudo commands normally:

```python
# Connect to the server
ssh_connect(host="your-server.com", username="admin")

# Execute sudo commands
ssh_run(session_id="session_id", cmd="sudo apt update")
ssh_run(session_id="session_id", cmd="sudo systemctl restart ssh")
ssh_run(session_id="session_id", cmd="sudo cat /etc/shadow")
```

### Command Chaining with Sudo

High permissibility also allows command chaining:

```python
# Multiple commands with sudo
ssh_run(session_id="session_id", cmd="sudo apt update && sudo apt upgrade -y")

# Piping with sudo
ssh_run(session_id="session_id", cmd="ps aux | grep ssh | sudo tee /tmp/ssh_processes.txt")

# Complex sudo operations
ssh_run(session_id="session_id", cmd="sudo systemctl status ssh && sudo journalctl -u ssh -n 50")
```

## 🛡️ Security Features

### Automatic Password Handling

The system automatically:
- Detects sudo password prompts
- Provides the configured password
- Handles various sudo prompt formats
- Logs password usage for security

### Supported Sudo Prompts

The system recognizes these sudo prompt patterns:
- `[sudo] password for user:`
- `[sudo] password for euler:`
- `Password:`
- `password:`
- `sudo: a terminal is required to read the password`
- `sudo: no tty present and no askpass program specified`

### Always Blocked Commands

Even with high permissibility, these dangerous commands are always blocked:
- `rm -rf /`
- `dd if=/dev/zero of=/dev/sda`
- `mkfs.ext4 /dev/sda`
- `fdisk /dev/sda`

## 🔍 Troubleshooting

### Common Issues

#### 1. "Command not allowed" Error
**Problem**: Sudo commands are being denied
**Solution**: Ensure permissibility level is set to "high"
```bash
export MCP_SSH_PERMISSIBILITY_LEVEL=high
```

#### 2. "Password required but not provided" Error
**Problem**: Sudo password prompt appears but no password is sent
**Solution**: Set the sudo password in configuration
```bash
export MCP_SSH_SUDO_PASSWORD=your_sudo_password
```
**Alternative**: Use MCP_PASSWORD as a fallback
```bash
export MCP_PASSWORD=your_default_password
```

#### 3. Command Hangs on Sudo (Timeout Error)
**Problem**: Command hangs waiting for password input and times out after 10 seconds
**Solution**: This is the most common issue. Check the following:

1. **Verify permissibility level**:
   ```bash
   export MCP_SSH_PERMISSIBILITY_LEVEL=high
   ```

2. **Set sudo password** (choose one):
   ```bash
   # Option A: Specific sudo password
   export MCP_SSH_SUDO_PASSWORD=your_sudo_password
   
   # Option B: Use MCP_PASSWORD as fallback
   export MCP_PASSWORD=your_default_password
   ```

3. **Enable debug mode** to see what's happening:
   ```bash
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   ```

4. **Check the logs** for password handling messages:
   - Look for "Sudo command detected with password available"
   - Look for "Proactively sending sudo password"
   - Look for "Password manager created with sudo password"

#### 4. "Sudo password not provided" Error
**Problem**: Sudo password is not being passed through
**Solution**: Verify the password is set in the correct environment variable
```bash
# Either set specific sudo password
export MCP_SSH_SUDO_PASSWORD=your_sudo_password

# Or use MCP_PASSWORD as fallback
export MCP_PASSWORD=your_default_password
```

### Debug Mode

Enable debug mode to see detailed password handling information:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

This will show:
- When sudo commands are detected
- When passwords are available
- When password managers are created
- When passwords are sent proactively
- Any password handling errors

### Testing Sudo Functionality

Use the test script to verify sudo functionality:

```bash
cd /path/to/remote-mcp
PYTHONPATH=/path/to/remote-mcp python test_sudo_password.py
```

### Recent Improvements

The system now includes several improvements to prevent sudo timeout issues:

1. **Proactive Password Handling**: For sudo commands, the system now proactively sends the password if no output is received
2. **Better Timeout Detection**: Sudo commands get specific timeout handling with better error messages
3. **Enhanced Debug Logging**: More detailed logging to help troubleshoot password issues
4. **MCP_PASSWORD Fallback**: Automatic fallback to MCP_PASSWORD when specific passwords aren't set

## 📋 Complete Example

Here's a complete example of setting up and using sudo with MCP SSH:

### 1. Environment Setup
```bash
# Set high permissibility
export MCP_SSH_PERMISSIBILITY_LEVEL=high

# Set sudo password (choose one option)
export MCP_SSH_SUDO_PASSWORD=your_sudo_password
# OR use MCP_PASSWORD as fallback for both SSH and sudo
export MCP_PASSWORD=your_default_password

# Set other SSH parameters
export MCP_SSH_HOST=your-server.com
export MCP_SSH_USER=admin
export MCP_SSH_KEY=/path/to/your/key

# Enable debug mode (optional)
export DEBUG=true
```

### 2. MCP Configuration
```json
{
  "mcpServers": {
    "production-ssh": {
      "command": "/usr/bin/python3",
      "args": ["/path/to/remote-mcp/start_mcp_server.py"],
      "env": {
        "MCP_SSH_PERMISSIBILITY_LEVEL": "high",
        "MCP_SSH_SUDO_PASSWORD": "your_sudo_password",
        "MCP_SSH_HOST": "your-server.com",
        "MCP_SSH_USER": "admin",
        "MCP_SSH_KEY": "/path/to/your/key",
        "DEBUG": "true"
      }
    }
  }
}
```

**Alternative using MCP_PASSWORD**:
```json
{
  "mcpServers": {
    "production-ssh": {
      "command": "/usr/bin/python3",
      "args": ["/path/to/remote-mcp/start_mcp_server.py"],
      "env": {
        "MCP_SSH_PERMISSIBILITY_LEVEL": "high",
        "MCP_PASSWORD": "your_default_password",
        "MCP_SSH_HOST": "your-server.com",
        "MCP_SSH_USER": "admin",
        "MCP_SSH_KEY": "/path/to/your/key",
        "DEBUG": "true"
      }
    }
  }
}
```

### 3. Usage
```python
# Connect
result = ssh_connect(host="your-server.com", username="admin")
session_id = result["session_id"]

# Use sudo commands
ssh_run(session_id=session_id, cmd="sudo apt update")
ssh_run(session_id=session_id, cmd="sudo systemctl status ssh")
ssh_run(session_id=session_id, cmd="sudo journalctl -u ssh -n 20")

# Command chaining
ssh_run(session_id=session_id, cmd="sudo apt update && sudo apt upgrade -y")

# Disconnect
ssh_disconnect(session_id=session_id)
```

## 🔒 Security Best Practices

### 1. Use Strong Passwords
- Use complex sudo passwords
- Consider using sudoers configuration for specific commands
- Regularly rotate passwords

### 2. Limit Sudo Access
- Only grant sudo access to necessary users
- Use specific sudoers rules instead of full sudo access
- Consider using `NOPASSWD` for specific commands

### 3. Monitor Usage
- Enable logging for sudo commands
- Monitor MCP SSH logs for sudo usage
- Set up alerts for suspicious sudo activity

### 4. Network Security
- Use SSH keys instead of passwords when possible
- Restrict SSH access to specific IP addresses
- Use VPN or bastion hosts for remote access

## 📚 Related Documentation

- [Permissibility Levels Implementation](PERMISSIBILITY_IMPLEMENTATION.md)
- [README.md](README.md) - Main project documentation
- [Configuration Examples](configs/) - Configuration file examples

## 🆘 Support

If you encounter issues with sudo functionality:

1. Check the debug logs for detailed information
2. Verify all configuration parameters are set correctly
3. Test with the provided test script
4. Check the troubleshooting section above
5. Review the security configuration on the target server

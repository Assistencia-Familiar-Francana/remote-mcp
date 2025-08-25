# MCP Remote SSH Server

A robust, SOLID-compliant Multi-Context Protocol (MCP) server for remote SSH operations with advanced password management and security features.

## 🚀 Features

- **SOLID Architecture**: Clean, maintainable code following SOLID principles
- **Advanced Password Management**: Environmental, interactive, and session-specific password handling
- **Security-First**: Comprehensive security patterns and command validation
- **Session Management**: Persistent SSH sessions with automatic cleanup
- **Tool Handlers**: Extensible tool system for SSH operations
- **Timeout Management**: Intelligent timeout handling to prevent hanging commands

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

Set up environment variables:

```bash
export MCP_SSH_HOST="your-host.com"
export MCP_SSH_USER="your-username"
export MCP_SSH_KEY="/path/to/your/ssh/key"
export MCP_SSH_SUDO_PASSWORD="your-sudo-password"  # Optional
export MCP_SSH_INTERACTIVE_PASSWORD="true"         # Optional
```

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

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review the test examples in `mcp_remote_ssh/tests/`
3. Check the demo scripts in `demos/`

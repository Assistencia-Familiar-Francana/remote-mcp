# Project Structure

This document provides a comprehensive overview of the MCP Remote SSH Server project structure after the cleanup and reorganization.

## 📁 Directory Structure

```
remote-mcp/
├── mcp_remote_ssh/                    # Main package
│   ├── __init__.py                    # Package initialization
│   ├── server.py                      # MCP server implementation
│   ├── session.py                     # SSH session management (refactored)
│   ├── session_manager.py             # Session lifecycle management
│   ├── tool_handlers.py               # Tool handler implementations
│   ├── config.py                      # Configuration management
│   ├── security.py                    # Security validation (refactored)
│   ├── security_patterns.py           # Security pattern management
│   ├── password_handler.py            # Password handling system
│   ├── interactive_password_service.py # Interactive password service
│   ├── examples/                      # Example configurations
│   │   └── host.json                  # Example host configuration
│   ├── tests/                         # Unit and integration tests
│   │   ├── __init__.py
│   │   ├── test_tool_handlers.py      # Tool handler tests
│   │   ├── test_password_functionality.py # Password functionality tests
│   │   ├── test_security.py           # Security tests
│   │   ├── test_session.py            # Session tests
│   │   ├── test_ssh_connection.py     # SSH connection tests
│   │   ├── test_mcp_config.py         # Configuration tests
│   │   ├── test_simple_ssh.py         # Simple SSH tests
│   │   ├── test_connections.py        # Connection tests
│   │   └── test_password_handler.py   # Password handler tests
│   └── node/                          # Node.js related files
│       └── package.json               # Node.js package configuration
├── docs/                              # Documentation
│   ├── README.md                      # Detailed API documentation
│   ├── PASSWORD_MANAGEMENT.md         # Password management guide
│   ├── DEPLOYMENT_GUIDE.md            # Deployment instructions
│   ├── CLOUDFLARE_DNS_SETUP.md        # Cloudflare DNS setup
│   ├── DUAL_MCP_SETUP.md              # Dual MCP setup guide
│   ├── NETWORK_OPTIMIZATION_PLAN.md   # Network optimization
│   ├── NETWORK_STATUS_SUMMARY.md      # Network status summary
│   ├── CURSOR_RESTART_GUIDE.md        # Cursor restart guide
│   └── FINAL_SUCCESS_SUMMARY.md       # Success summary
├── demos/                             # Example demonstrations
│   ├── demo.py                        # Basic demo
│   ├── simple_demo.py                 # Simple demonstration
│   ├── standalone_demo.py             # Standalone demo
│   ├── working_demo.py                # Working demo
│   ├── final_demo.py                  # Final demo
│   └── simple_connection_test.py      # Connection test demo
├── scripts/                           # Utility scripts
│   ├── bourbaki_tunnel_config.yaml    # Bourbaki tunnel config
│   ├── ff_tunnel_config.yaml          # FF tunnel config
│   └── mcp_ssh_config.yaml            # MCP SSH configuration
├── configs/                           # Configuration files
│   ├── enhanced_mcp_with_subdomains.json # Enhanced MCP config
│   └── updated_mcp_config.json        # Updated MCP config
├── start_mcp_server.py                # Server startup script
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── env.example                        # Environment variables example
├── .gitignore                         # Git ignore rules
└── README.md                          # Main project README
```

## 🔧 Core Components

### Main Package (`mcp_remote_ssh/`)

#### Core Files
- **`server.py`**: MCP server implementation with tool registration
- **`session.py`**: SSH session management (refactored with SOLID principles)
- **`session_manager.py`**: Session lifecycle and cleanup management
- **`tool_handlers.py`**: Tool handler implementations following SOLID principles
- **`config.py`**: Configuration management with environment variable support

#### Security Components
- **`security.py`**: Security validation (refactored to use pattern manager)
- **`security_patterns.py`**: Security pattern management system
- **`password_handler.py`**: Password handling system with multiple strategies
- **`interactive_password_service.py`**: Interactive password service

#### Testing (`tests/`)
- **`test_tool_handlers.py`**: Tool handler unit tests
- **`test_password_functionality.py`**: Password functionality tests
- **`test_security.py`**: Security pattern tests
- **`test_session.py`**: Session management tests
- **`test_ssh_connection.py`**: SSH connection tests
- **`test_mcp_config.py`**: Configuration tests
- **`test_simple_ssh.py`**: Simple SSH functionality tests
- **`test_connections.py`**: Connection management tests
- **`test_password_handler.py`**: Password handler tests

## 📚 Documentation (`docs/`)

- **`README.md`**: Detailed API documentation
- **`PASSWORD_MANAGEMENT.md`**: Comprehensive password management guide
- **`DEPLOYMENT_GUIDE.md`**: Deployment and configuration instructions
- **`CLOUDFLARE_DNS_SETUP.md`**: Cloudflare DNS configuration
- **`DUAL_MCP_SETUP.md`**: Dual MCP server setup
- **`NETWORK_OPTIMIZATION_PLAN.md`**: Network optimization strategies
- **`NETWORK_STATUS_SUMMARY.md`**: Network status documentation
- **`CURSOR_RESTART_GUIDE.md`**: Cursor IDE restart instructions
- **`FINAL_SUCCESS_SUMMARY.md`**: Project success summary

## 🎯 Demonstrations (`demos/`)

- **`demo.py`**: Basic MCP server demonstration
- **`simple_demo.py`**: Simple SSH connection demo
- **`standalone_demo.py`**: Standalone server demonstration
- **`working_demo.py`**: Working example demonstration
- **`final_demo.py`**: Final project demonstration
- **`simple_connection_test.py`**: Connection testing demo

## ⚙️ Configuration (`configs/`)

- **`enhanced_mcp_with_subdomains.json`**: Enhanced MCP configuration
- **`updated_mcp_config.json`**: Updated MCP server configuration

## 🔧 Scripts (`scripts/`)

- **`bourbaki_tunnel_config.yaml`**: Bourbaki tunnel configuration
- **`ff_tunnel_config.yaml`**: FF tunnel configuration
- **`mcp_ssh_config.yaml`**: MCP SSH server configuration

## 🏗️ Architecture Overview

### SOLID Principles Implementation

1. **Single Responsibility Principle (SRP)**
   - Each class has a single, well-defined responsibility
   - `SessionManager` handles session lifecycle
   - `SecurityPatternManager` handles security patterns
   - `ToolHandler` classes handle specific tool operations

2. **Open/Closed Principle (OCP)**
   - Easy to extend with new tool handlers
   - New security patterns can be added without modification
   - Password handlers can be extended

3. **Liskov Substitution Principle (LSP)**
   - All handlers follow consistent interfaces
   - Security patterns can be substituted
   - Password handlers are interchangeable

4. **Interface Segregation Principle (ISP)**
   - Focused interfaces for different concerns
   - `ToolHandler` interface for tool operations
   - `SecurityPattern` interface for security patterns
   - `PasswordHandler` interface for password handling

5. **Dependency Inversion Principle (DIP)**
   - High-level modules depend on abstractions
   - `ToolHandlerFactory` depends on `ToolHandler` interface
   - `SecurityManager` depends on `SecurityPatternManager` abstraction

### Key Design Patterns

1. **Factory Pattern**: `ToolHandlerFactory` creates appropriate handlers
2. **Strategy Pattern**: Multiple password handling strategies
3. **Observer Pattern**: Password service with callback system
4. **Singleton Pattern**: Global configuration and service instances

## 🧪 Testing Strategy

### Test Organization
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Functional Tests**: End-to-end functionality testing

### Test Categories
- **Tool Handler Tests**: Test each tool handler implementation
- **Security Tests**: Test security pattern matching and validation
- **Session Tests**: Test session management and lifecycle
- **Password Tests**: Test password handling and interactive features
- **Configuration Tests**: Test configuration loading and validation

## 🔒 Security Features

1. **Command Validation**: All commands validated against security patterns
2. **Password Security**: Secure password handling with timeouts
3. **Session Isolation**: Each session isolated and managed separately
4. **Audit Logging**: Comprehensive logging for security auditing
5. **Pattern Matching**: Extensible security pattern system

## 🚀 Deployment

### Requirements
- Python 3.8+
- Required packages listed in `requirements.txt`
- SSH key or password authentication
- Network access to target hosts

### Configuration
- Environment variables for SSH connection
- Optional password configuration
- Security pattern customization
- Session management settings

## 📈 Future Enhancements

1. **Additional Tool Handlers**: More SSH operation tools
2. **Enhanced Security Patterns**: More sophisticated security rules
3. **Plugin System**: Extensible plugin architecture
4. **Monitoring**: Enhanced monitoring and metrics
5. **API Documentation**: OpenAPI/Swagger documentation

## 🛠️ Development Workflow

1. **Feature Development**: Add new tool handlers or security patterns
2. **Testing**: Write comprehensive tests for new features
3. **Documentation**: Update relevant documentation
4. **Code Review**: Follow SOLID principles and coding standards
5. **Integration**: Ensure backward compatibility

This structure provides a clean, maintainable, and extensible codebase that follows best practices and SOLID principles.

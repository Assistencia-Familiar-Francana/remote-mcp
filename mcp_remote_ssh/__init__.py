"""MCP Remote SSH Server - Secure remote SSH access via Model Context Protocol."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import core modules that don't require MCP dependencies
from .config import get_config
from .security import get_security_manager

# Conditionally import modules that need additional dependencies
try:
    from .session import get_session_manager
    SESSION_AVAILABLE = True
except ImportError:
    SESSION_AVAILABLE = False

try:
    from .server import main
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False

__all__ = [
    "get_config", 
    "get_security_manager"
]

if SESSION_AVAILABLE:
    __all__.append("get_session_manager")

if SERVER_AVAILABLE:
    __all__.append("main")

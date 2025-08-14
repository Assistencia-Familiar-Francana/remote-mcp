#!/usr/bin/env python3
"""
Standalone MCP server startup script.
This ensures the server can be run from any directory.
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

# Import and run the server
try:
    from mcp_remote_ssh.server import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Error importing MCP server: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install modelcontextprotocol paramiko pyyaml python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"Error starting MCP server: {e}")
    sys.exit(1)

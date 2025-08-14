#!/usr/bin/env python3
"""Test script to verify MCP server configuration."""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_remote_ssh.config import get_config

def test_config():
    """Test the configuration loading."""
    print("Testing MCP server configuration...")
    
    # Check environment variables
    print("\nEnvironment variables:")
    env_vars = [
        'MCP_SSH_HOST',
        'MCP_SSH_USER', 
        'MCP_SSH_KEY',
        'MCP_SSH_PORT',
        'MCP_SSH_PROXY_COMMAND'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        print(f"  {var}: {value}")
    
    # Load config
    print("\nConfiguration:")
    config = get_config()
    print(f"  SSH Host: {config.ssh.default_host}")
    print(f"  SSH User: {config.ssh.default_username}")
    print(f"  SSH Key: {config.ssh.key_path}")
    print(f"  SSH Port: {config.ssh.default_port}")
    print(f"  Proxy Command: {config.ssh.proxy_command}")
    
    # Test proxy command replacement
    if config.ssh.proxy_command and config.ssh.default_host:
        proxy_cmd = config.ssh.proxy_command.replace('%h', config.ssh.default_host)
        print(f"\nProxy command with host replacement:")
        print(f"  Original: {config.ssh.proxy_command}")
        print(f"  Replaced: {proxy_cmd}")

if __name__ == "__main__":
    test_config()

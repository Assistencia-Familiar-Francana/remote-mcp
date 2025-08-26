#!/usr/bin/env python3
"""
Demo script for MCP Remote SSH permissibility levels.

This script demonstrates how different permissibility levels affect command execution.
Run this script to see how the security system works with low, medium, and high permissibility levels.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import the mcp_remote_ssh module
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_remote_ssh.config import PermissibilityLevel, SecurityConfig
from mcp_remote_ssh.security import SecurityManager

def test_permissibility_levels():
    """Test different permissibility levels with various commands."""
    
    print("🔒 MCP Remote SSH Permissibility Level Demo")
    print("=" * 50)
    
    # Test commands for different scenarios
    test_commands = [
        # Basic read operations (should work in all levels)
        "ls -la",
        "cat /etc/hostname",
        "ps aux",
        "df -h",
        
        # File operations (medium+)
        "cp file1 file2",
        "mv file1 file2",
        "rm file1",
        "mkdir testdir",
        
        # System administration (medium+)
        "systemctl status ssh",
        "journalctl -u ssh",
        "kill 1234",
        
        # Sudo operations (high only)
        "sudo apt update",
        "sudo systemctl restart ssh",
        "sudo reboot",
        
        # Command chaining (high only)
        "ls && echo 'success'",
        "ps aux | grep ssh",
        "cat file.txt | head -10",
        
        # Dangerous operations (should be blocked)
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda",
        "fdisk /dev/sda",
        
        # Complex patterns
        "sudo rm -rf /tmp/*",
        "ls && sudo apt update",
        "ps aux | grep ssh && sudo systemctl restart ssh",
    ]
    
    # Test each permissibility level
    for level in [PermissibilityLevel.LOW, PermissibilityLevel.MEDIUM, PermissibilityLevel.HIGH]:
        print(f"\n📋 Testing {level.value.upper()} Permissibility Level")
        print("-" * 40)
        
        # Create a security config with this level
        config = SecurityConfig(permissibility_level=level)
        
        # Create a new security manager with this config
        from mcp_remote_ssh.config import Config
        test_config = Config(security=config)
        
        # We need to monkey patch the global config temporarily
        import mcp_remote_ssh.config as config_module
        original_config = config_module.config
        config_module.config = test_config
        
        try:
            security_manager = SecurityManager()
            
            # Get permissibility info
            info = security_manager.get_permissibility_info()
            print(f"Allowed commands: {info['allowed_commands_count']}")
            print(f"Denied patterns: {info['denied_patterns_count']}")
            
            # Test each command
            for cmd in test_commands:
                result = security_manager.validate_command(cmd)
                status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
                print(f"{status}: {cmd}")
                if not result.allowed:
                    print(f"    Reason: {result.reason}")
        finally:
            # Restore original config
            config_module.config = original_config
        
        print()

def test_environment_variable():
    """Test setting permissibility level via environment variable."""
    
    print("\n🌍 Environment Variable Test")
    print("-" * 30)
    
    # Test different environment variable values
    test_values = ["low", "medium", "high", "invalid", ""]
    
    for value in test_values:
        if value:
            os.environ['MCP_SSH_PERMISSIBILITY_LEVEL'] = value
        else:
            os.environ.pop('MCP_SSH_PERMISSIBILITY_LEVEL', None)
        
        # Create config (this will read from environment)
        config = SecurityConfig()
        print(f"Environment value: '{value}' -> Permissibility level: {config.permissibility_level.value}")

def test_json_config():
    """Test loading permissibility level from JSON config."""
    
    print("\n📄 JSON Configuration Test")
    print("-" * 30)
    
    # Create a temporary config file
    config_content = """
security:
  permissibility_level: high
  max_output_bytes: 10485760
  max_output_lines: 10000
  command_timeout_seconds: 300
  rate_limit_per_minute: 500
  max_sessions: 20
"""
    
    config_file = Path("temp_config.yaml")
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Set environment variable to use this config
        os.environ['MCP_SSH_CONFIG'] = str(config_file)
        
        # Create config (this will read from file)
        config = SecurityConfig()
        print(f"Config file permissibility level: {config.permissibility_level.value}")
        
    finally:
        # Clean up
        if config_file.exists():
            config_file.unlink()
        os.environ.pop('MCP_SSH_CONFIG', None)

def main():
    """Main demo function."""
    
    print("🚀 Starting MCP Remote SSH Permissibility Demo")
    print("This demo shows how the permissibility system works with different security levels.")
    print()
    
    # Test 1: Different permissibility levels
    test_permissibility_levels()
    
    # Test 2: Environment variable configuration
    test_environment_variable()
    
    # Test 3: JSON configuration
    test_json_config()
    
    print("\n✅ Demo completed!")
    print("\n📚 Summary:")
    print("- LOW: Basic read-only operations only")
    print("- MEDIUM: Read operations + safe write operations")
    print("- HIGH: Full administrative access with sudo")
    print("\n🔧 Configuration methods:")
    print("- Environment variable: MCP_SSH_PERMISSIBILITY_LEVEL")
    print("- JSON config file: security.permissibility_level")
    print("- Default: medium (if not specified)")

if __name__ == "__main__":
    main()

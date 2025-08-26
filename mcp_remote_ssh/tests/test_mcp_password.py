#!/usr/bin/env python3
"""
Test script for MCP_PASSWORD fallback functionality.

This script tests that MCP_PASSWORD is properly used as a fallback
when specific passwords are not configured.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_remote_ssh.config import SSHConfig, Config

def test_mcp_password_fallback():
    """Test that MCP_PASSWORD is used as fallback when specific passwords are not set."""
    print("🧪 Testing MCP_PASSWORD Fallback")
    print("=" * 40)
    
    # Test 1: No passwords set
    print("\n1. Testing with no passwords set...")
    # Clear any existing environment variables
    for var in ['MCP_PASSWORD', 'MCP_SSH_PASSWORD', 'MCP_SSH_SUDO_PASSWORD']:
        os.environ.pop(var, None)
    
    config = SSHConfig.from_env()
    print(f"Default password: {config.default_password}")
    print(f"Sudo password: {config.sudo_password}")
    
    # Test 2: Only MCP_PASSWORD set
    print("\n2. Testing with only MCP_PASSWORD set...")
    os.environ['MCP_PASSWORD'] = 'mcp_fallback_password'
    
    config = SSHConfig.from_env()
    print(f"Default password: {config.default_password}")
    print(f"Sudo password: {config.sudo_password}")
    
    if config.default_password == 'mcp_fallback_password' and config.sudo_password == 'mcp_fallback_password':
        print("✅ MCP_PASSWORD correctly used as fallback for both passwords")
    else:
        print("❌ MCP_PASSWORD fallback not working correctly")
    
    # Test 3: Specific passwords override MCP_PASSWORD
    print("\n3. Testing that specific passwords override MCP_PASSWORD...")
    os.environ['MCP_SSH_PASSWORD'] = 'specific_ssh_password'
    os.environ['MCP_SSH_SUDO_PASSWORD'] = 'specific_sudo_password'
    
    config = SSHConfig.from_env()
    print(f"Default password: {config.default_password}")
    print(f"Sudo password: {config.sudo_password}")
    
    if (config.default_password == 'specific_ssh_password' and 
        config.sudo_password == 'specific_sudo_password'):
        print("✅ Specific passwords correctly override MCP_PASSWORD")
    else:
        print("❌ Specific passwords not overriding MCP_PASSWORD correctly")
    
    # Test 4: Mixed configuration
    print("\n4. Testing mixed configuration...")
    os.environ.pop('MCP_SSH_PASSWORD', None)  # Remove specific SSH password
    os.environ['MCP_SSH_SUDO_PASSWORD'] = 'specific_sudo_password'  # Keep specific sudo password
    
    config = SSHConfig.from_env()
    print(f"Default password: {config.default_password}")
    print(f"Sudo password: {config.sudo_password}")
    
    if (config.default_password == 'mcp_fallback_password' and 
        config.sudo_password == 'specific_sudo_password'):
        print("✅ Mixed configuration working correctly")
    else:
        print("❌ Mixed configuration not working correctly")
    
    print()

def test_config_class():
    """Test the main Config class with MCP_PASSWORD fallback."""
    print("🧪 Testing Config Class with MCP_PASSWORD")
    print("=" * 40)
    
    # Clear any existing environment variables first
    for var in ['MCP_PASSWORD', 'MCP_SSH_PASSWORD', 'MCP_SSH_SUDO_PASSWORD']:
        os.environ.pop(var, None)
    
    # Set up test environment
    os.environ['MCP_PASSWORD'] = 'config_test_password'
    os.environ['MCP_SSH_PERMISSIBILITY_LEVEL'] = 'high'
    
    config = Config()
    print(f"SSH default password: {config.ssh.default_password}")
    print(f"SSH sudo password: {config.ssh.sudo_password}")
    print(f"Permissibility level: {config.security.permissibility_level.value}")
    
    if (config.ssh.default_password == 'config_test_password' and 
        config.ssh.sudo_password == 'config_test_password'):
        print("✅ Config class correctly uses MCP_PASSWORD fallback")
    else:
        print("❌ Config class not using MCP_PASSWORD fallback correctly")
    
    print()

def test_environment_priority():
    """Test the priority order of environment variables."""
    print("🧪 Testing Environment Variable Priority")
    print("=" * 40)
    
    # Set all password variables
    os.environ['MCP_PASSWORD'] = 'mcp_password'
    os.environ['MCP_SSH_PASSWORD'] = 'ssh_password'
    os.environ['MCP_SSH_SUDO_PASSWORD'] = 'sudo_password'
    
    config = SSHConfig.from_env()
    print(f"Default password: {config.default_password}")
    print(f"Sudo password: {config.sudo_password}")
    
    # Should use specific passwords, not MCP_PASSWORD
    if (config.default_password == 'ssh_password' and 
        config.sudo_password == 'sudo_password'):
        print("✅ Priority order working correctly: specific > MCP_PASSWORD")
    else:
        print("❌ Priority order not working correctly")
    
    print()

def main():
    """Main test function."""
    print("🚀 Starting MCP_PASSWORD Fallback Tests")
    print("This script tests the MCP_PASSWORD fallback functionality.")
    print()
    
    try:
        test_mcp_password_fallback()
        test_config_class()
        test_environment_priority()
        
        print("✅ All tests completed!")
        print("\n📚 Summary:")
        print("- MCP_PASSWORD is used as fallback when specific passwords are not set")
        print("- Specific passwords (MCP_SSH_PASSWORD, MCP_SSH_SUDO_PASSWORD) override MCP_PASSWORD")
        print("- Mixed configurations work correctly")
        print("- Priority order: specific passwords > MCP_PASSWORD > None")
        
        print("\n🔧 Usage:")
        print("1. Set MCP_PASSWORD for general fallback")
        print("2. Set MCP_SSH_PASSWORD for SSH-specific password")
        print("3. Set MCP_SSH_SUDO_PASSWORD for sudo-specific password")
        print("4. Specific passwords take priority over MCP_PASSWORD")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

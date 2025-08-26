#!/usr/bin/env python3
"""
Test script for sudo password handling fixes.

This script tests the improved sudo password handling to ensure
configured passwords are used automatically and complex commands work.
"""

import os
import sys
from pathlib import Path

# Set environment variables before importing modules
os.environ['MCP_SSH_PERMISSIBILITY_LEVEL'] = 'high'
os.environ['MCP_PASSWORD'] = 'test_password'

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration():
    """Test that the configuration is correct."""
    print("🧪 Testing Configuration")
    print("=" * 40)
    
    # Check environment variables
    mcp_password = os.getenv('MCP_PASSWORD')
    mcp_ssh_sudo_password = os.getenv('MCP_SSH_SUDO_PASSWORD')
    mcp_ssh_permissibility = os.getenv('MCP_SSH_PERMISSIBILITY_LEVEL')
    
    print(f"MCP_PASSWORD: {'✅ Set' if mcp_password else '❌ Not set'}")
    print(f"MCP_SSH_SUDO_PASSWORD: {'✅ Set' if mcp_ssh_sudo_password else '❌ Not set'}")
    print(f"MCP_SSH_PERMISSIBILITY_LEVEL: {mcp_ssh_permissibility or '❌ Not set'}")
    
    if mcp_ssh_permissibility == 'high':
        print("✅ Permissibility level is set to high")
    else:
        print("❌ Permissibility level should be 'high' for sudo commands")
    
    print()

def test_password_priority():
    """Test password priority order."""
    print("🧪 Testing Password Priority")
    print("=" * 40)
    
    from mcp_remote_ssh.config import SSHConfig
    
    # Test 1: Only MCP_PASSWORD
    print("\n1. Testing MCP_PASSWORD only...")
    os.environ['MCP_PASSWORD'] = 'test_password'
    os.environ.pop('MCP_SSH_SUDO_PASSWORD', None)
    
    config = SSHConfig.from_env()
    print(f"Expected: test_password, Got: {config.sudo_password}")
    
    if config.sudo_password == 'test_password':
        print("✅ MCP_PASSWORD correctly used as fallback")
    else:
        print("❌ MCP_PASSWORD fallback not working")
    
    # Test 2: Both passwords (MCP_SSH_SUDO_PASSWORD should take precedence)
    print("\n2. Testing both passwords...")
    os.environ['MCP_SSH_SUDO_PASSWORD'] = 'specific_sudo_password'
    
    config = SSHConfig.from_env()
    print(f"Expected: specific_sudo_password, Got: {config.sudo_password}")
    
    if config.sudo_password == 'specific_sudo_password':
        print("✅ MCP_SSH_SUDO_PASSWORD correctly overrides MCP_PASSWORD")
    else:
        print("❌ MCP_SSH_SUDO_PASSWORD override not working")
    
    print()

def test_password_manager():
    """Test password manager creation."""
    print("🧪 Testing Password Manager Creation")
    print("=" * 40)
    
    from mcp_remote_ssh.password_handler import create_password_manager
    
    # Test with sudo password
    manager = create_password_manager(sudo_password='test_sudo_password')
    sudo_handler = manager.get_handler_for_type('sudo')
    
    if sudo_handler and hasattr(sudo_handler, 'sudo_password') and sudo_handler.sudo_password == 'test_sudo_password':
        print("✅ Password manager created with sudo password")
    else:
        print("❌ Password manager not created correctly with sudo password")
    
    # Test handler detection
    if sudo_handler and sudo_handler.can_handle('sudo'):
        print("✅ Sudo handler can handle sudo prompts")
    else:
        print("❌ Sudo handler cannot handle sudo prompts")
    
    print()

def test_security_patterns():
    """Test that sudo commands are allowed."""
    print("🧪 Testing Security Patterns")
    print("=" * 40)
    
    from mcp_remote_ssh.security import SecurityManager
    
    security = SecurityManager()
    
    test_commands = [
        "sudo whoami",
        "sudo ls /root",
        "sudo systemctl status ssh",
        "sudo cat /etc/passwd",
        "sudo -u root whoami",
    ]
    
    for cmd in test_commands:
        result = security.validate_command(cmd)
        if result.allowed:
            print(f"✅ '{cmd}' - Allowed")
        else:
            print(f"❌ '{cmd}' - {result.reason}")
    
    print()

def main():
    """Main test function."""
    print("🚀 Starting Sudo Fixes Tests")
    print("This script tests the improved sudo password handling.")
    print()
    
    try:
        test_configuration()
        test_password_priority()
        test_password_manager()
        test_security_patterns()
        
        print("✅ All tests completed!")
        print("\n📚 Summary of fixes:")
        print("- Enhanced proactive password handling")
        print("- More aggressive timeout detection")
        print("- Better password priority handling")
        print("- Improved debug logging")
        print("- Fixed security pattern validation")
        
        print("\n🔧 To test with MCP servers:")
        print("1. Ensure MCP_SSH_PERMISSIBILITY_LEVEL=high")
        print("2. Set MCP_PASSWORD or MCP_SSH_SUDO_PASSWORD")
        print("3. Test sudo commands without explicit sudo_password parameter")
        print("4. Check debug logs for password handling messages")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

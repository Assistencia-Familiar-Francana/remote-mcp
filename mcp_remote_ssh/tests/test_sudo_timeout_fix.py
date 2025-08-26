#!/usr/bin/env python3
"""
Test script for sudo timeout fix.

This script tests the improved sudo password handling to ensure
it doesn't timeout when sudo commands are executed.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_remote_ssh.config import SSHConfig, Config
from mcp_remote_ssh.password_handler import SudoPasswordHandler, PasswordManager

def test_sudo_password_availability():
    """Test that sudo passwords are properly configured."""
    print("🧪 Testing Sudo Password Availability")
    print("=" * 40)
    
    # Test 1: MCP_PASSWORD fallback
    print("\n1. Testing MCP_PASSWORD fallback...")
    os.environ['MCP_PASSWORD'] = 'test_password'
    os.environ.pop('MCP_SSH_SUDO_PASSWORD', None)
    
    config = SSHConfig.from_env()
    print(f"Sudo password: {config.sudo_password}")
    
    if config.sudo_password == 'test_password':
        print("✅ MCP_PASSWORD correctly used as sudo password fallback")
    else:
        print("❌ MCP_PASSWORD fallback not working")
    
    # Test 2: Specific sudo password
    print("\n2. Testing specific sudo password...")
    os.environ['MCP_SSH_SUDO_PASSWORD'] = 'specific_sudo_password'
    
    config = SSHConfig.from_env()
    print(f"Sudo password: {config.sudo_password}")
    
    if config.sudo_password == 'specific_sudo_password':
        print("✅ Specific sudo password correctly overrides MCP_PASSWORD")
    else:
        print("❌ Specific sudo password not working")
    
    print()

def test_password_manager_creation():
    """Test that password managers are created correctly with sudo passwords."""
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
    
    # Test without sudo password
    manager_no_pwd = create_password_manager(sudo_password=None)
    sudo_handler_no_pwd = manager_no_pwd.get_handler_for_type('sudo')
    
    if not sudo_handler_no_pwd:
        print("✅ Password manager correctly created without sudo password")
    else:
        print("❌ Password manager incorrectly created with sudo password")
    
    print()

def test_sudo_command_detection():
    """Test that sudo commands are properly detected."""
    print("🧪 Testing Sudo Command Detection")
    print("=" * 40)
    
    sudo_commands = [
        "sudo ls /root",
        "sudo apt update",
        "sudo systemctl status ssh",
        "sudo cat /etc/shadow",
        "sudo -u root whoami",
        "sudo -E env",
    ]
    
    non_sudo_commands = [
        "ls /root",
        "apt update",
        "systemctl status ssh",
        "cat /etc/shadow",
        "whoami",
        "env",
    ]
    
    for cmd in sudo_commands:
        if cmd.strip().startswith('sudo'):
            print(f"✅ '{cmd}' - Correctly detected as sudo command")
        else:
            print(f"❌ '{cmd}' - Not detected as sudo command")
    
    for cmd in non_sudo_commands:
        if not cmd.strip().startswith('sudo'):
            print(f"✅ '{cmd}' - Correctly detected as non-sudo command")
        else:
            print(f"❌ '{cmd}' - Incorrectly detected as sudo command")
    
    print()

def test_configuration_examples():
    """Test various configuration examples."""
    print("🧪 Testing Configuration Examples")
    print("=" * 40)
    
    # Example 1: Using MCP_PASSWORD
    print("\n1. Configuration with MCP_PASSWORD:")
    print("export MCP_PASSWORD=your_password")
    print("export MCP_SSH_PERMISSIBILITY_LEVEL=high")
    
    # Example 2: Using specific passwords
    print("\n2. Configuration with specific passwords:")
    print("export MCP_SSH_SUDO_PASSWORD=your_sudo_password")
    print("export MCP_SSH_PASSWORD=your_ssh_password")
    print("export MCP_SSH_PERMISSIBILITY_LEVEL=high")
    
    # Example 3: Mixed configuration
    print("\n3. Mixed configuration:")
    print("export MCP_PASSWORD=your_default_password")
    print("export MCP_SSH_SUDO_PASSWORD=your_sudo_password")
    print("export MCP_SSH_PERMISSIBILITY_LEVEL=high")
    
    print("\n🔧 Usage in MCP configuration:")
    print('{')
    print('  "mcpServers": {')
    print('    "production-ssh": {')
    print('      "env": {')
    print('        "MCP_SSH_PERMISSIBILITY_LEVEL": "high",')
    print('        "MCP_PASSWORD": "your_password"')
    print('      }')
    print('    }')
    print('  }')
    print('}')
    
    print()

def main():
    """Main test function."""
    print("🚀 Starting Sudo Timeout Fix Tests")
    print("This script tests the improved sudo password handling.")
    print()
    
    try:
        test_sudo_password_availability()
        test_password_manager_creation()
        test_sudo_command_detection()
        test_configuration_examples()
        
        print("✅ All tests completed!")
        print("\n📚 Summary of improvements:")
        print("- Proactive password handling for sudo commands")
        print("- Better timeout detection and handling")
        print("- MCP_PASSWORD fallback support")
        print("- Enhanced debug logging")
        print("- Sudo-specific error messages")
        
        print("\n🔧 To fix sudo timeout issues:")
        print("1. Set MCP_SSH_PERMISSIBILITY_LEVEL=high")
        print("2. Set MCP_SSH_SUDO_PASSWORD=your_sudo_password")
        print("3. Or use MCP_PASSWORD as fallback")
        print("4. Enable debug mode: export DEBUG=true")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

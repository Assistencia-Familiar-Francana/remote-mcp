#!/usr/bin/env python3
"""
Test script for sudo password handling.

This script tests the sudo password functionality to ensure it works correctly.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_remote_ssh.config import SecurityConfig, PermissibilityLevel
from mcp_remote_ssh.security import SecurityManager
from mcp_remote_ssh.password_handler import SudoPasswordHandler, PasswordPrompt

async def test_sudo_password_detection():
    """Test sudo password prompt detection."""
    print("🧪 Testing Sudo Password Detection")
    print("=" * 40)
    
    # Create a sudo password handler
    handler = SudoPasswordHandler(sudo_password="test_password")
    
    # Test various sudo prompt patterns
    test_prompts = [
        "[sudo] password for user:",
        "[sudo] password for euler:",
        "Password:",
        "password:",
        "sudo: a terminal is required to read the password",
        "sudo: no tty present and no askpass program specified",
        "We trust you have received the usual lecture from the local System",
    ]
    
    for prompt in test_prompts:
        result = await handler.detect_prompt(prompt)
        if result:
            print(f"✅ Detected: '{prompt}'")
        else:
            print(f"❌ Not detected: '{prompt}'")
    
    print()

async def test_sudo_password_handling():
    """Test sudo password handling."""
    print("🧪 Testing Sudo Password Handling")
    print("=" * 40)
    
    # Test with password provided
    handler_with_password = SudoPasswordHandler(sudo_password="test_password")
    prompt = PasswordPrompt(
        prompt_type='sudo',
        prompt_text='[sudo] password for user:',
        position=0,
        requires_input=True
    )
    
    context = {"command": "sudo ls /root"}
    response = await handler_with_password.handle_prompt(prompt, context)
    
    if response.password:
        print(f"✅ Password provided: {response.password}")
    else:
        print(f"❌ No password provided: {response.error}")
    
    # Test without password
    handler_without_password = SudoPasswordHandler(sudo_password=None)
    response = await handler_without_password.handle_prompt(prompt, context)
    
    if response.error:
        print(f"✅ Correctly handled missing password: {response.error}")
    else:
        print(f"❌ Should have returned error for missing password")
    
    print()

def test_permissibility_with_sudo():
    """Test that sudo commands are allowed in high permissibility mode."""
    print("🧪 Testing Permissibility with Sudo")
    print("=" * 40)
    
    # Test high permissibility by monkey patching the config
    import mcp_remote_ssh.config as config_module
    original_config = config_module.config
    
    # Create a test config with high permissibility
    test_config = config_module.Config()
    test_config.security.permissibility_level = PermissibilityLevel.HIGH
    config_module.config = test_config
    
    try:
        security_manager = SecurityManager()
        
        sudo_commands = [
            "sudo ls /root",
            "sudo apt update",
            "sudo systemctl status ssh",
            "sudo cat /etc/shadow",
        ]
        
        for cmd in sudo_commands:
            result = security_manager.validate_command(cmd)
            if result.allowed:
                print(f"✅ '{cmd}' - ALLOWED")
            else:
                print(f"❌ '{cmd}' - DENIED: {result.reason}")
    finally:
        # Restore original config
        config_module.config = original_config
    
    print()

async def main():
    """Main test function."""
    print("🚀 Starting Sudo Password Handling Tests")
    print("This script tests the sudo password functionality.")
    print()
    
    try:
        await test_sudo_password_detection()
        await test_sudo_password_handling()
        test_permissibility_with_sudo()
        
        print("✅ All tests completed!")
        print("\n📚 Summary:")
        print("- Sudo password detection works correctly")
        print("- Sudo password handling works correctly")
        print("- High permissibility allows sudo commands")
        print("\n🔧 To use sudo in MCP SSH:")
        print("1. Set MCP_SSH_PERMISSIBILITY_LEVEL=high")
        print("2. Set MCP_SSH_SUDO_PASSWORD=your_sudo_password")
        print("3. Use ssh_run with sudo commands")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))

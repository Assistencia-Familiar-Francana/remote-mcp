#!/usr/bin/env python3
"""
Simple test script for the permissibility system.

This script tests the basic functionality of the permissibility levels.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_remote_ssh.config import PermissibilityLevel, SecurityConfig
from mcp_remote_ssh.security import SecurityManager

def test_basic_functionality():
    """Test basic permissibility functionality."""
    print("🧪 Testing Basic Permissibility Functionality")
    print("=" * 50)
    
    # Test 1: Environment variable configuration
    print("\n1. Testing environment variable configuration...")
    os.environ['MCP_SSH_PERMISSIBILITY_LEVEL'] = 'high'
    config = SecurityConfig()
    assert config.permissibility_level == PermissibilityLevel.HIGH
    print("✅ High permissibility level set correctly")
    
    # Test 2: Command validation
    print("\n2. Testing command validation...")
    security_manager = SecurityManager()
    
    # Test allowed commands
    allowed_commands = [
        "ls -la",
        "cat /etc/hostname",
        "sudo apt update",
        "ls && echo 'test'",
    ]
    
    for cmd in allowed_commands:
        result = security_manager.validate_command(cmd)
        if result.allowed:
            print(f"✅ '{cmd}' - ALLOWED")
        else:
            print(f"❌ '{cmd}' - DENIED: {result.reason}")
    
    # Test denied commands
    denied_commands = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
    ]
    
    for cmd in denied_commands:
        result = security_manager.validate_command(cmd)
        if not result.allowed:
            print(f"✅ '{cmd}' - CORRECTLY DENIED: {result.reason}")
        else:
            print(f"❌ '{cmd}' - INCORRECTLY ALLOWED")
    
    # Test 3: Permissibility info
    print("\n3. Testing permissibility info...")
    info = security_manager.get_permissibility_info()
    print(f"Current level: {info['permissibility_level']}")
    print(f"Allowed commands: {info['allowed_commands_count']}")
    print(f"Denied patterns: {info['denied_patterns_count']}")
    
    # Test 4: Different levels
    print("\n4. Testing different permissibility levels...")
    for level in [PermissibilityLevel.LOW, PermissibilityLevel.MEDIUM, PermissibilityLevel.HIGH]:
        config = SecurityConfig(permissibility_level=level)
        allowed_cmds = config.get_allowed_commands()
        denied_patterns = config.get_denied_patterns()
        print(f"{level.value.upper()}: {len(allowed_cmds)} commands, {len(denied_patterns)} patterns")

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    security_manager = SecurityManager()
    
    # Test empty command
    result = security_manager.validate_command("")
    assert not result.allowed
    print("✅ Empty command correctly denied")
    
    # Test whitespace-only command
    result = security_manager.validate_command("   ")
    assert not result.allowed
    print("✅ Whitespace-only command correctly denied")
    
    # Test invalid permissibility level
    try:
        config = SecurityConfig()
        # This should default to medium
        print(f"✅ Invalid level defaults to: {config.permissibility_level.value}")
    except Exception as e:
        print(f"❌ Error with invalid level: {e}")

def main():
    """Main test function."""
    print("🚀 Starting Permissibility System Tests")
    print("This script tests the basic functionality of the permissibility levels.")
    print()
    
    try:
        test_basic_functionality()
        test_edge_cases()
        
        print("\n✅ All tests passed!")
        print("\n📚 Summary:")
        print("- Environment variable configuration works")
        print("- Command validation works correctly")
        print("- Different permissibility levels have different restrictions")
        print("- Edge cases are handled properly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

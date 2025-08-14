#!/usr/bin/env python3
"""
Demo script for MCP Remote SSH Server
This script demonstrates the key functionality without requiring MCP client integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_remote_ssh.session import get_session_manager, SSHSession
from mcp_remote_ssh.security import get_security_manager
from mcp_remote_ssh.config import get_config

async def demo_session_management():
    """Demonstrate SSH session management."""
    print("🔗 SSH Session Management Demo")
    print("=" * 40)
    
    session_manager = get_session_manager()
    
    # Create a session (won't actually connect without real credentials)
    print("📝 Creating SSH session...")
    session = await session_manager.create_session(
        session_id="demo-session",
        host="100.65.56.110", 
        port=22,
        username="abel"
    )
    
    print(f"✅ Session created: {session.session_id}")
    print(f"   Host: {session.host}")
    print(f"   Username: {session.username}")
    print(f"   Connected: {session.connected}")
    
    # List sessions
    sessions = session_manager.list_sessions()
    print(f"📋 Active sessions: {len(sessions)}")
    
    for session_info in sessions:
        print(f"   - {session_info.session_id}: {session_info.username}@{session_info.host}")
    
    # Clean up
    await session_manager.remove_session("demo-session")
    print("🧹 Session cleaned up")
    print()

def demo_security_validation():
    """Demonstrate security validation."""
    print("🔒 Security Validation Demo")
    print("=" * 40)
    
    security = get_security_manager()
    
    # Test various commands
    test_commands = [
        "ls -la",                    # Should pass
        "kubectl get pods",          # Should pass
        "rm -rf /",                 # Should fail
        "sudo passwd",              # Should fail
        "cat /etc/passwd",          # Should pass
        "systemctl status nginx",   # Should pass
        "ls && rm file",            # Should fail (dangerous pattern)
    ]
    
    for cmd in test_commands:
        result = security.validate_command(cmd)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"{status}: {cmd}")
        if not result.allowed:
            print(f"         Reason: {result.reason}")
    
    print()
    
    # Test secret redaction
    print("🔒 Secret Redaction Demo")
    print("-" * 25)
    
    text_with_secrets = """
    API_KEY=sk-1234567890abcdef1234567890abcdef12345678
    GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
    Some normal text here
    PASSWORD=mysecretpassword123
    """
    
    print("Original text:")
    print(text_with_secrets)
    
    redacted = security.redact_secrets(text_with_secrets)
    print("Redacted text:")
    print(redacted)
    print()

def demo_config():
    """Demonstrate configuration."""
    print("⚙️  Configuration Demo")
    print("=" * 40)
    
    config = get_config()
    
    print(f"SSH Default Host: {config.ssh.default_host}")
    print(f"SSH Default Port: {config.ssh.default_port}")
    print(f"SSH Default User: {config.ssh.default_username}")
    print(f"Debug Mode: {config.debug}")
    print(f"Max Sessions: {config.security.max_sessions}")
    print(f"Command Timeout: {config.security.command_timeout_seconds}s")
    print(f"Max Output: {config.security.max_output_bytes} bytes")
    print(f"Allowed Commands: {len(config.security.allowed_commands)}")
    
    # Show first few allowed commands
    print("First 10 allowed commands:")
    for cmd in config.security.allowed_commands[:10]:
        print(f"  - {cmd}")
    
    print()

def demo_file_validation():
    """Demonstrate file path validation."""
    print("📁 File Path Validation Demo")
    print("=" * 40)
    
    security = get_security_manager()
    
    test_paths = [
        "/home/user/file.txt",      # Should pass
        "/var/log/app.log",         # Should pass
        "/etc/passwd",              # Should fail
        "/tmp/tempfile",            # Should pass
        "~/.ssh/id_rsa",            # Should fail
        "/proc/version",            # Should fail
        "./local-file.txt",         # Should pass
    ]
    
    for path in test_paths:
        result = security.validate_file_path(path)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"{status}: {path}")
        if not result.allowed:
            print(f"         Reason: {result.reason}")
    
    print()

async def main():
    """Run all demos."""
    print("🚀 MCP Remote SSH Server Demo")
    print("=" * 50)
    print("This demo shows the key features without requiring")
    print("actual SSH connections or MCP client integration.")
    print("=" * 50)
    print()
    
    # Configuration demo
    demo_config()
    
    # Security demos
    demo_security_validation()
    demo_file_validation()
    
    # Session management demo
    await demo_session_management()
    
    print("🎉 Demo completed!")
    print()
    print("Next steps:")
    print("1. Install dependencies: uv sync")
    print("2. Configure your SSH credentials in .env")
    print("3. Start server: python -m mcp_remote_ssh.server")
    print("4. Configure Cursor with the MCP server")
    print("5. Ask Cursor to connect to your remote machines!")

if __name__ == "__main__":
    asyncio.run(main())

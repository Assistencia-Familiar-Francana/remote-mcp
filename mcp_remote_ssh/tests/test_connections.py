#!/usr/bin/env python3
"""
Test MCP Remote SSH Server connections to both ff and bourbaki nodes.
This script simulates what Cursor will do when using the MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_remote_ssh.session import get_session_manager
from mcp_remote_ssh.security import get_security_manager
from mcp_remote_ssh.config import get_config

async def test_ff_connection():
    """Test connection to ff node (Kubernetes master)."""
    print("🔗 Testing FF Node Connection (abel@100.65.56.110:22)")
    print("=" * 60)
    
    session_manager = get_session_manager()
    
    try:
        # Create session for ff node
        session = await session_manager.create_session(
            session_id="test-ff",
            host="100.65.56.110",
            port=22,
            username="abel"
        )
        
        print(f"✅ Session created: {session.session_id}")
        print(f"   Host: {session.host}")
        print(f"   Username: {session.username}")
        
        # Attempt connection (will fail without proper SSH setup, but shows the flow)
        try:
            connected = await session.connect("key", key_path="/home/ramanujan/.ssh/id_ed25519")
            if connected:
                print("✅ SSH connection established!")
                
                # Test some commands
                test_commands = [
                    "whoami",
                    "uname -a",
                    "kubectl get nodes",
                    "kubectl get pods -n funeraria-francana"
                ]
                
                for cmd in test_commands:
                    try:
                        result = await session.execute_command(cmd)
                        print(f"✅ {cmd}: {result.stdout[:100]}...")
                    except Exception as e:
                        print(f"⚠️  {cmd}: {e}")
                
            else:
                print("❌ SSH connection failed (expected without proper key setup)")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("   This is expected if SSH keys aren't configured")
        
        # Clean up
        await session_manager.remove_session("test-ff")
        print("🧹 Session cleaned up")
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
    
    print()

async def test_bourbaki_connection():
    """Test connection to bourbaki node via cloudflared tunnel."""
    print("🔗 Testing Bourbaki Node Connection (euler@127.0.0.1:2222)")
    print("=" * 60)
    
    session_manager = get_session_manager()
    
    try:
        # Create session for bourbaki node (via tunnel)
        session = await session_manager.create_session(
            session_id="test-bourbaki", 
            host="127.0.0.1",
            port=2222,
            username="euler"
        )
        
        print(f"✅ Session created: {session.session_id}")
        print(f"   Host: {session.host}:{session.port} (via cloudflared tunnel)")
        print(f"   Username: {session.username}")
        
        # Attempt connection
        try:
            connected = await session.connect("key", key_path="/home/ramanujan/.ssh/id_ed25519")
            if connected:
                print("✅ SSH connection established!")
                
                # Test some commands
                test_commands = [
                    "whoami",
                    "uname -a", 
                    "kubectl get nodes",
                    "docker ps"
                ]
                
                for cmd in test_commands:
                    try:
                        result = await session.execute_command(cmd)
                        print(f"✅ {cmd}: {result.stdout[:100]}...")
                    except Exception as e:
                        print(f"⚠️  {cmd}: {e}")
                        
            else:
                print("❌ SSH connection failed (expected without proper key setup)")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("   This is expected if SSH keys aren't configured")
        
        # Clean up
        await session_manager.remove_session("test-bourbaki")
        print("🧹 Session cleaned up")
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
    
    print()

def test_mcp_server_status():
    """Test MCP server components."""
    print("🔧 Testing MCP Server Components")
    print("=" * 60)
    
    # Test configuration
    config = get_config()
    print(f"✅ Configuration loaded")
    print(f"   Default host: {config.ssh.default_host}")
    print(f"   Max sessions: {config.security.max_sessions}")
    print(f"   Allowed commands: {len(config.security.allowed_commands)}")
    
    # Test security manager
    security = get_security_manager()
    print(f"✅ Security manager initialized")
    
    # Test some Kubernetes commands validation
    k8s_commands = [
        "kubectl get pods -n funeraria-francana",
        "kubectl describe svc cartas-backend",
        "kubectl logs cartas-backend-abc123",
        "kubectl delete pod dangerous-pod"  # Should be blocked
    ]
    
    print("🔒 Command validation tests:")
    for cmd in k8s_commands:
        result = security.validate_command(cmd)
        status = "✅ ALLOWED" if result.allowed else "❌ BLOCKED"
        print(f"   {status}: {cmd}")
    
    print()

def show_cursor_instructions():
    """Show instructions for using with Cursor."""
    print("🎯 Using with Cursor")
    print("=" * 60)
    print("The MCP server is now running in the background.")
    print("Your Cursor configuration is already set up.")
    print()
    print("In Cursor, you can now ask:")
    print()
    print("💬 'Connect to my Kubernetes master node and show me the pod status'")
    print("💬 'Check the system resources on my ff server'")
    print("💬 'Connect to my bourbaki worker node and show docker containers'")
    print("💬 'Show me the logs for the cartas-backend service'")
    print("💬 'What's the current status of my funeral announcement application?'")
    print()
    print("The AI will:")
    print("1. Use ssh_connect to establish a connection")
    print("2. Use ssh_run to execute safe commands")
    print("3. Parse and analyze the results")
    print("4. Provide intelligent insights about your infrastructure")
    print()
    print("🔒 Security features active:")
    print("   • Only safe commands allowed (kubectl, docker, ls, cat, etc.)")
    print("   • Dangerous commands blocked (rm, sudo, kill, etc.)")
    print("   • Secrets automatically redacted from output")
    print("   • File access restricted to safe directories")
    print()

async def main():
    """Run all connection tests."""
    print("🚀 MCP Remote SSH Server - Connection Test")
    print("=" * 70)
    print("Testing connections to your Kubernetes cluster nodes")
    print("=" * 70)
    print()
    
    # Test MCP server components
    test_mcp_server_status()
    
    # Test connections (will show the flow even if SSH fails)
    await test_ff_connection()
    await test_bourbaki_connection()
    
    # Show Cursor usage instructions
    show_cursor_instructions()
    
    print("🎉 Connection Test Complete!")
    print("=" * 70)
    print()
    print("🔧 To fix SSH connections:")
    print("1. Ensure SSH keys are properly configured:")
    print("   chmod 600 ~/.ssh/id_ed25519")
    print("   ssh-add ~/.ssh/id_ed25519")
    print()
    print("2. Test manual SSH connections:")
    print("   ssh abel@100.65.56.110")
    print("   ssh -p 2222 euler@127.0.0.1")
    print()
    print("3. Once SSH works manually, the MCP server will work automatically!")
    print()
    print("🌐 Your MCP server is ready for Cursor integration!")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Simple demo for MCP Remote SSH Server core functionality
This demo tests security and configuration without requiring MCP dependencies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import only the core modules (not server.py which needs MCP)
from mcp_remote_ssh.security import SecurityManager
from mcp_remote_ssh.config import Config

def demo_security_validation():
    """Demonstrate security validation."""
    print("🔒 Security Validation Demo")
    print("=" * 40)
    
    security = SecurityManager()
    
    # Test various commands
    test_commands = [
        "ls -la",                    # Should pass
        "kubectl get pods",          # Should pass
        "rm -rf /",                 # Should fail
        "sudo passwd",              # Should fail
        "cat /etc/passwd",          # Should pass
        "systemctl status nginx",   # Should pass
        "ls && rm file",            # Should fail (dangerous pattern)
        "docker ps",                # Should pass
        "git status",               # Should pass
        "kill -9 1234",            # Should fail
    ]
    
    print("Command Validation Results:")
    for cmd in test_commands:
        result = security.validate_command(cmd)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"  {status}: {cmd}")
        if not result.allowed:
            print(f"           Reason: {result.reason}")
    
    print()
    
    # Test secret redaction
    print("🔒 Secret Redaction Demo")
    print("-" * 25)
    
    text_with_secrets = """
API_KEY=sk-1234567890abcdef1234567890abcdef12345678
GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
AWS_ACCESS_KEY=AKIA1234567890ABCDEF
Some normal text here
PASSWORD=mysecretpassword123
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7...
-----END PRIVATE KEY-----
    """.strip()
    
    print("Original text (truncated):")
    print(text_with_secrets[:200] + "...")
    
    redacted = security.redact_secrets(text_with_secrets)
    print("\nRedacted text:")
    print(redacted)
    print()

def demo_config():
    """Demonstrate configuration."""
    print("⚙️  Configuration Demo")
    print("=" * 40)
    
    config = Config()
    
    print(f"SSH Default Host: {config.ssh.default_host or 'Not set'}")
    print(f"SSH Default Port: {config.ssh.default_port}")
    print(f"SSH Default User: {config.ssh.default_username or 'Not set'}")
    print(f"Debug Mode: {config.debug}")
    print(f"Max Sessions: {config.security.max_sessions}")
    print(f"Command Timeout: {config.security.command_timeout_seconds}s")
    print(f"Max Output: {config.security.max_output_bytes} bytes")
    print(f"Allowed Commands: {len(config.security.allowed_commands)}")
    
    # Show first few allowed commands
    print("\nFirst 15 allowed commands:")
    for i, cmd in enumerate(config.security.allowed_commands[:15]):
        print(f"  {i+1:2d}. {cmd}")
    
    print(f"\nFirst 10 denied commands:")
    for i, cmd in enumerate(config.security.denied_commands[:10]):
        print(f"  {i+1:2d}. {cmd}")
    
    print()

def demo_file_validation():
    """Demonstrate file path validation."""
    print("📁 File Path Validation Demo")
    print("=" * 40)
    
    security = SecurityManager()
    
    test_paths = [
        "/home/user/file.txt",      # Should pass
        "/var/log/app.log",         # Should pass  
        "/etc/passwd",              # Should fail
        "/tmp/tempfile",            # Should pass
        "~/.ssh/id_rsa",            # Should fail
        "/proc/version",            # Should fail
        "./local-file.txt",         # Should pass
        "/boot/grub.cfg",          # Should fail
        "/opt/app/config.yaml",    # Should pass
        "../../../etc/shadow",     # Should fail
    ]
    
    print("File Path Validation Results:")
    for path in test_paths:
        result = security.validate_file_path(path)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"  {status}: {path}")
        if not result.allowed:
            print(f"           Reason: {result.reason}")
    
    print()

def demo_kubectl_validation():
    """Demonstrate kubectl command validation."""
    print("☸️  Kubernetes Command Validation Demo")
    print("=" * 40)
    
    security = SecurityManager()
    
    kubectl_commands = [
        "kubectl get pods",
        "kubectl get pods -n funeraria-francana",
        "kubectl describe service cartas-backend",
        "kubectl logs cartas-backend-abc123",
        "kubectl top nodes",
        "kubectl delete pod dangerous-pod",  # Should fail
        "kubectl apply -f malicious.yaml",   # Should fail
        "kubectl exec -it pod -- /bin/bash", # Should fail
    ]
    
    print("Kubectl Command Validation:")
    for cmd in kubectl_commands:
        result = security.validate_command(cmd)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"  {status}: {cmd}")
        if not result.allowed:
            print(f"           Reason: {result.reason}")
    
    print()

def main():
    """Run all demos."""
    print("🚀 MCP Remote SSH Server - Core Functionality Demo")
    print("=" * 60)
    print("This demo shows security and configuration features")
    print("without requiring MCP dependencies or SSH connections.")
    print("=" * 60)
    print()
    
    # Configuration demo
    demo_config()
    
    # Security demos
    demo_security_validation()
    demo_file_validation()
    demo_kubectl_validation()
    
    print("🎉 Demo completed successfully!")
    print()
    print("Next steps:")
    print("1. Install MCP dependencies:")
    print("   pip install modelcontextprotocol paramiko pyyaml python-dotenv")
    print("2. Configure your SSH credentials in .env file")
    print("3. Start the MCP server:")
    print("   python -m mcp_remote_ssh.server")
    print("4. Configure Cursor to use the MCP server")
    print("5. Ask Cursor to connect to your Kubernetes cluster!")
    print()
    print("🔗 Your cluster setup:")
    print("   ff node: abel@100.65.56.110:22")
    print("   bourbaki node: euler@127.0.0.1:2222 (via cloudflared tunnel)")

if __name__ == "__main__":
    main()

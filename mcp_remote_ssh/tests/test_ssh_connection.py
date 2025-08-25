#!/usr/bin/env python3
"""Test SSH connection with proxy command."""

import paramiko
import os
import sys

def test_ssh_connection():
    """Test SSH connection with proxy command."""
    print("Testing SSH connection with proxy command...")
    
    # Get environment variables
    host = os.getenv('MCP_SSH_HOST', 'ssh.buddhilw.com')
    username = os.getenv('MCP_SSH_USER', 'abel')
    key_path = os.getenv('MCP_SSH_KEY', '/home/ramanujan/.ssh/id_ed25519')
    proxy_command = os.getenv('MCP_SSH_PROXY_COMMAND', 'cloudflared access ssh --hostname %h')
    
    print(f"Host: {host}")
    print(f"Username: {username}")
    print(f"Key path: {key_path}")
    print(f"Proxy command: {proxy_command}")
    
    try:
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Prepare connection parameters
        connect_kwargs = {
            'hostname': host,
            'port': 22,
            'username': username,
            'key_filename': key_path,
            'timeout': 30,
        }
        
        # Add proxy command
        if proxy_command:
            # Replace %h with hostname
            proxy_cmd = proxy_command.replace('%h', host)
            print(f"Using proxy command: {proxy_cmd}")
            connect_kwargs['sock'] = paramiko.ProxyCommand(proxy_cmd)
        
        # Connect
        print("Attempting to connect...")
        client.connect(**connect_kwargs)
        
        print("Connection successful!")
        
        # Test command execution
        stdin, stdout, stderr = client.exec_command('echo "SSH connection test successful"')
        result = stdout.read().decode().strip()
        print(f"Command result: {result}")
        
        # Close connection
        client.close()
        print("Connection closed successfully.")
        
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ssh_connection()

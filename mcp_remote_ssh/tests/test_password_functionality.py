#!/usr/bin/env python3
"""Test script for the new password functionality."""

import asyncio
import sys
import os
sys.path.append('..')

from interactive_password_service import get_password_service, PasswordRequest
from password_handler import create_password_manager
from config import get_config

async def test_password_service():
    """Test the interactive password service."""
    print("Testing Interactive Password Service...")
    
    # Get the password service
    password_service = get_password_service()
    
    # Set up a simple callback that returns a test password
    async def test_callback(request: PasswordRequest):
        print(f"Password requested for: {request.prompt_text}")
        print(f"Session: {request.session_id}")
        print(f"Host: {request.host}")
        print(f"Command: {request.command}")
        return "test_password_123"
    
    password_service.set_password_callback(test_callback)
    
    # Test requesting a password
    password = await password_service.request_password(
        prompt_text="[sudo] password for user:",
        prompt_type="sudo",
        session_id="test_session",
        host="test.host.com",
        username="test_user",
        command="sudo systemctl status k3s"
    )
    
    print(f"Received password: {password}")
    
    # Test listing pending requests
    pending = password_service.get_pending_requests()
    print(f"Pending requests: {len(pending)}")

async def test_password_manager():
    """Test the password manager with interactive support."""
    print("\nTesting Password Manager...")
    
    # Create a password manager with interactive support
    async def test_callback(prompt, context):
        print(f"Interactive callback called for: {prompt.prompt_text}")
        return "interactive_password_456"
    
    manager = create_password_manager(
        sudo_password="config_sudo_password",
        interactive_callback=test_callback,
        enable_interactive=True
    )
    
    # Test detecting a password prompt
    test_output = "[sudo] password for user:"
    context = {"session_id": "test", "command": "sudo ls"}
    
    response = await manager.detect_and_handle_prompt(test_output, context)
    if response and response.password:
        print(f"Password manager provided: {response.password}")
    else:
        print("Password manager did not provide password")

async def test_config():
    """Test the configuration with password settings."""
    print("\nTesting Configuration...")
    
    config = get_config()
    print(f"Interactive password enabled: {config.ssh.enable_interactive_password}")
    print(f"Default password set: {config.ssh.default_password is not None}")
    print(f"Sudo password set: {config.ssh.sudo_password is not None}")

async def main():
    """Main test function."""
    print("=== Password Functionality Test ===\n")
    
    await test_config()
    await test_password_service()
    await test_password_manager()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())

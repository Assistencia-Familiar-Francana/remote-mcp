#!/bin/bash
set -euo pipefail

echo "🔐 Passwordless Sudo Setup for MCP"
echo "=================================="
echo ""

echo "This script helps set up passwordless sudo for specific commands"
echo "that the MCP server needs to run (systemctl, journalctl, etc.)"
echo ""

echo "📋 Commands to run on each server:"
echo ""

echo "1️⃣  On FF node (abel@ff):"
echo "   sudo visudo"
echo "   Add this line at the end:"
echo "   abel ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/journalctl, /usr/bin/kubectl"
echo ""

echo "2️⃣  On Bourbaki node (euler@bourbaki):"
echo "   sudo visudo"
echo "   Add this line at the end:"
echo "   euler ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/journalctl, /usr/bin/docker"
echo ""

echo "3️⃣  Alternative: Create sudoers drop-in files:"
echo ""

cat << 'EOF'
# On FF node:
echo "abel ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/journalctl, /usr/bin/kubectl" | sudo tee /etc/sudoers.d/mcp-abel

# On Bourbaki node:
echo "euler ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/journalctl, /usr/bin/docker" | sudo tee /etc/sudoers.d/mcp-euler

# Set correct permissions:
sudo chmod 440 /etc/sudoers.d/mcp-*
EOF

echo ""
echo "4️⃣  Test the setup:"
echo "   sudo systemctl status duckdns.timer  # Should work without password"
echo "   sudo journalctl -u duckdns.service --since '1 hour ago'"
echo ""

echo "⚠️  Security Notes:"
echo "   - Only specific commands are granted passwordless access"
echo "   - Users still need password for other sudo operations"
echo "   - This is safer than full passwordless sudo"
echo ""

echo "5️⃣  Update MCP security config:"
echo "   Remove 'sudo' from denied_commands in mcp_ssh_config.yaml"
echo "   Add specific sudo commands to allowed_commands"

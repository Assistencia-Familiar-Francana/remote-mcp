#!/bin/bash

# MCP Remote SSH Server Setup Script
# This script sets up the MCP server for your specific Cloudflare tunnel configuration

set -e

echo "🚀 Setting up MCP Remote SSH Server"
echo "===================================="

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: Please run this script from the remote-mcp directory"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python -m pip install modelcontextprotocol paramiko pyyaml python-dotenv

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env configuration file..."
    cat > .env << EOF
# MCP Remote SSH Configuration for your Cloudflare setup

# Default connection (ff node - Kubernetes master)
MCP_SSH_HOST=100.65.56.110
MCP_SSH_PORT=22
MCP_SSH_USER=abel
MCP_SSH_KEY=/home/ramanujan/.ssh/id_ed25519

# Connection timeouts
MCP_SSH_CONNECT_TIMEOUT=30
MCP_SSH_KEEPALIVE=30

# Logging
DEBUG=true
LOG_LEVEL=INFO

# Alternative setup for bourbaki node (uncomment to use):
# First run: cloudflared access tcp --hostname bourbaki.buddhilw.com --listener 127.0.0.1:2222
# MCP_SSH_HOST=127.0.0.1
# MCP_SSH_PORT=2222
# MCP_SSH_USER=euler
EOF
    echo "✅ Created .env file with your Cloudflare tunnel configuration"
else
    echo "ℹ️  .env file already exists, skipping creation"
fi

# Test the security system
echo "🔒 Testing security system..."
python standalone_demo.py > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    echo "✅ Security system test passed"
else
    echo "❌ Security system test failed"
    exit 1
fi

# Check SSH key exists
SSH_KEY="/home/ramanujan/.ssh/id_ed25519"
if [[ -f "$SSH_KEY" ]]; then
    echo "✅ SSH key found at $SSH_KEY"
else
    echo "⚠️  SSH key not found at $SSH_KEY"
    echo "   Make sure your SSH key path is correct in .env"
fi

# Test SSH connectivity (optional)
echo "🔗 Testing SSH connectivity to ff node..."
if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes abel@100.65.56.110 'echo "SSH connection successful"' 2>/dev/null; then
    echo "✅ SSH connection to ff node successful"
else
    echo "⚠️  SSH connection to ff node failed"
    echo "   This is expected if you haven't set up SSH keys yet"
fi

# Update Cursor MCP configuration
CURSOR_CONFIG="/home/ramanujan/.cursor/mcp.json"
if [[ -f "$CURSOR_CONFIG" ]]; then
    echo "✅ Cursor MCP configuration already exists"
    echo "   Configuration: $CURSOR_CONFIG"
else
    echo "📝 Cursor MCP configuration not found"
    echo "   Expected location: $CURSOR_CONFIG"
    echo "   Please create it manually or restart Cursor"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo "================================"
echo ""
echo "🚀 Next steps:"
echo "1. Start the MCP server:"
echo "   python -m mcp_remote_ssh.server"
echo ""
echo "2. In Cursor, ask:"
echo "   'Connect to my Kubernetes cluster and show me the pod status'"
echo ""
echo "3. Or try:"
echo "   'Check the system resources on my ff node'"
echo "   'Show me the logs for the cartas-backend service'"
echo ""
echo "🔧 Troubleshooting:"
echo "- If SSH fails, check your key permissions: chmod 600 ~/.ssh/id_ed25519"
echo "- For bourbaki access, start the tunnel first:"
echo "  cloudflared access tcp --hostname bourbaki.buddhilw.com --listener 127.0.0.1:2222"
echo "- Check MCP server logs for connection issues"
echo ""
echo "🌐 Your cluster endpoints:"
echo "   ff (master): abel@100.65.56.110:22"  
echo "   bourbaki (worker): euler@127.0.0.1:2222 (via tunnel)"

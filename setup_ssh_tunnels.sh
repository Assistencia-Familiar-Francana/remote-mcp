#!/bin/bash
set -euo pipefail

echo "🚀 Setting up Cloudflare SSH Tunnels"
echo "====================================="
echo ""

echo "📋 Instructions for tunnel setup:"
echo ""

echo "1️⃣  On FF node (abel@ff):"
echo "   Copy the ff_tunnel_config.yaml to ~/.cloudflared/config.yml:"
echo "   scp ff_tunnel_config.yaml abel@ff:~/.cloudflared/config.yml"
echo ""
echo "   Then on FF node, run:"
echo "   cloudflared service install"
echo "   sudo systemctl enable cloudflared"
echo "   sudo systemctl start cloudflared"
echo ""

echo "2️⃣  On Bourbaki node (euler@bourbaki):"
echo "   First, find the credentials file:"
echo "   ls -la ~/.cloudflared/"
echo ""
echo "   Copy the bourbaki_tunnel_config.yaml and update credentials path:"
echo "   scp bourbaki_tunnel_config.yaml euler@bourbaki:~/.cloudflared/config.yml"
echo ""
echo "   Then on Bourbaki node, run:"
echo "   cloudflared service install"
echo "   sudo systemctl enable cloudflared"
echo "   sudo systemctl start cloudflared"
echo ""

echo "3️⃣  Test SSH access:"
echo "   ssh abel@ff.buddhilw.com"
echo "   ssh euler@bourbaki.buddhilw.com"
echo ""

echo "4️⃣  Update MCP configuration:"
echo "   Use ff.buddhilw.com and bourbaki.buddhilw.com as hostnames"
echo ""

echo "✅ Benefits after setup:"
echo "   - Direct SSH access through Cloudflare"
echo "   - No manual tunnel startup needed"
echo "   - Works through CGNAT"
echo "   - Automatic SSL/security"

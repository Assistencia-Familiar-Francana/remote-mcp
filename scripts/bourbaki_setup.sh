#!/bin/bash
set -euo pipefail

echo "🔧 Bourbaki Node SSH Tunnel Setup"
echo "=================================="
echo ""

echo "📋 Steps to execute on Bourbaki node (euler@bourbaki):"
echo ""

echo "1️⃣  Check if cloudflared is installed:"
echo "   which cloudflared"
echo "   cloudflared --version"
echo ""

echo "2️⃣  Find the credentials file:"
echo "   ls -la ~/.cloudflared/"
echo "   # Look for: 34a5ee95-a090-4c2d-b1a3-749f9265e3c8.json"
echo ""

echo "3️⃣  Update tunnel config with correct credentials path:"
echo "   # If credentials file has different name, update bourbaki_tunnel_config.yaml"
echo "   # credentials-file: /home/euler/.cloudflared/ACTUAL_FILENAME.json"
echo ""

echo "4️⃣  Install tunnel service:"
echo "   cp bourbaki_tunnel_config.yaml ~/.cloudflared/config.yml"
echo "   cloudflared service install"
echo "   sudo systemctl enable cloudflared"
echo "   sudo systemctl start cloudflared"
echo ""

echo "5️⃣  Verify service:"
echo "   sudo systemctl status cloudflared"
echo "   sudo journalctl -u cloudflared --since '5 minutes ago'"
echo ""

echo "6️⃣  Test SSH access:"
echo "   ssh euler@bourbaki.buddhilw.com"
echo ""

echo "✅ Expected result:"
echo "   SSH access working through Cloudflare tunnel"
echo "   No more need for manual tunnel startup"

#!/bin/bash
set -euo pipefail

echo "🔍 Testing Cloudflare SSH Tunnels"
echo "================================="
echo ""

echo "1️⃣  Testing FF node connection..."
if timeout 10s ssh -o ConnectTimeout=5 -o BatchMode=yes abel@ff.buddhilw.com 'echo "✅ FF SSH tunnel working: $(hostname) - $(whoami)"' 2>/dev/null; then
    echo "✅ FF node: SUCCESS"
else
    echo "❌ FF node: FAILED"
    echo "   - Check if tunnel is running: sudo systemctl status cloudflared"
    echo "   - Check DNS resolution: dig ff.buddhilw.com"
fi

echo ""
echo "2️⃣  Testing Bourbaki node connection..."
if timeout 10s ssh -o ConnectTimeout=5 -o BatchMode=yes euler@bourbaki.buddhilw.com 'echo "✅ Bourbaki SSH tunnel working: $(hostname) - $(whoami)"' 2>/dev/null; then
    echo "✅ Bourbaki node: SUCCESS"
else
    echo "❌ Bourbaki node: FAILED"
    echo "   - Check if tunnel is running: sudo systemctl status cloudflared"
    echo "   - Check DNS resolution: dig bourbaki.buddhilw.com"
fi

echo ""
echo "3️⃣  Testing system information gathering..."
if timeout 10s ssh -o ConnectTimeout=5 -o BatchMode=yes abel@ff.buddhilw.com 'uptime && kubectl get nodes --no-headers | wc -l' 2>/dev/null; then
    echo "✅ FF system info: SUCCESS"
else
    echo "❌ FF system info: FAILED"
fi

if timeout 10s ssh -o ConnectTimeout=5 -o BatchMode=yes euler@bourbaki.buddhilw.com 'uptime && docker ps --format "table {{.Names}}" | tail -n +2 | wc -l' 2>/dev/null; then
    echo "✅ Bourbaki system info: SUCCESS"
else
    echo "❌ Bourbaki system info: FAILED"
fi

echo ""
echo "🎯 Summary:"
echo "   If both nodes show SUCCESS, you can update MCP configuration"
echo "   and test AI-powered remote management through Cursor!"

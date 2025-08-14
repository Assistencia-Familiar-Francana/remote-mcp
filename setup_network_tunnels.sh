#!/bin/bash
# Network Tunnels Setup Script for CGNAT + DuckDNS + Cloudflare

set -euo pipefail

echo "🌐 Setting up Enhanced Network Tunnels for MCP SSH Access"
echo "========================================================="

# Configuration
DOMAIN="buddhilw.com"
TUNNEL_DIR="$HOME/.cloudflared"
LOG_DIR="$HOME/logs/tunnels"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$TUNNEL_DIR"

# Function to start tunnel with logging
start_tunnel() {
    local name="$1"
    local hostname="$2" 
    local listener="$3"
    local logfile="$LOG_DIR/${name}.log"
    
    echo "🔗 Starting tunnel: $name"
    echo "   Hostname: $hostname"
    echo "   Listener: $listener"
    echo "   Log: $logfile"
    
    # Check if tunnel is already running
    if pgrep -f "$hostname" > /dev/null; then
        echo "   ✅ Tunnel already running"
        return 0
    fi
    
    # Start tunnel in background
    nohup cloudflared access tcp \
        --hostname "$hostname" \
        --listener "$listener" \
        > "$logfile" 2>&1 &
    
    local pid=$!
    echo "   🚀 Started with PID: $pid"
    sleep 2
    
    # Verify tunnel is running
    if kill -0 "$pid" 2>/dev/null; then
        echo "   ✅ Tunnel confirmed running"
    else
        echo "   ❌ Tunnel failed to start"
        cat "$logfile"
        return 1
    fi
}

# Function to check tunnel status
check_tunnel() {
    local name="$1"
    local listener="$2"
    
    echo "🔍 Checking tunnel: $name"
    
    # Check if port is listening
    if netstat -tuln | grep "$listener" > /dev/null; then
        echo "   ✅ Listening on $listener"
        return 0
    else
        echo "   ❌ Not listening on $listener"
        return 1
    fi
}

echo ""
echo "🔧 Phase 1: Core SSH Tunnels"
echo "=============================="

# FF Node SSH Tunnel (backup to direct access)
start_tunnel "ff-ssh" "ff.$DOMAIN" "127.0.0.1:2223"

# Bourbaki SSH Tunnel (existing, verify it's running)
if check_tunnel "bourbaki-ssh" "127.0.0.1:2222"; then
    echo "✅ Bourbaki SSH tunnel already active"
else
    echo "🔗 Starting Bourbaki SSH tunnel"
    start_tunnel "bourbaki-ssh" "bourbaki.$DOMAIN" "127.0.0.1:2222"
fi

echo ""
echo "🔧 Phase 2: Application Tunnels"
echo "==============================="

# Web Application Tunnels
start_tunnel "app-frontend" "app.$DOMAIN" "127.0.0.1:3000"
start_tunnel "app-backend" "api.$DOMAIN" "127.0.0.1:8080"

# Kubernetes API Tunnel
start_tunnel "k8s-api" "k8s.$DOMAIN" "127.0.0.1:6443"

echo ""
echo "🔧 Phase 3: Verification"
echo "========================"

# Test all tunnels
TUNNELS=(
    "ff-ssh:127.0.0.1:2223"
    "bourbaki-ssh:127.0.0.1:2222" 
    "app-frontend:127.0.0.1:3000"
    "app-backend:127.0.0.1:8080"
    "k8s-api:127.0.0.1:6443"
)

echo "Active tunnels:"
for tunnel_info in "${TUNNELS[@]}"; do
    IFS=':' read -r name listener <<< "$tunnel_info"
    if check_tunnel "$name" "$listener"; then
        echo "  ✅ $name"
    else
        echo "  ❌ $name (not running)"
    fi
done

echo ""
echo "🔧 Phase 4: Generate MCP Configuration"
echo "======================================"

# Create enhanced MCP configuration
cat > "$HOME/enhanced_mcp.json" << EOF
{
  "mcpServers": {
    "ff-primary": {
      "command": "/home/ramanujan/anaconda3/bin/python",
      "args": ["/home/ramanujan/PP/funeraria/remote-mcp/start_mcp_server.py"],
      "cwd": "/home/ramanujan/PP/funeraria/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "100.65.56.110",
        "MCP_SSH_USER": "abel", 
        "MCP_SSH_KEY": "/home/ramanujan/.ssh/id_ed25519",
        "MCP_SSH_PORT": "22",
        "MCP_SSH_FALLBACK_HOST": "127.0.0.1",
        "MCP_SSH_FALLBACK_PORT": "2223",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO"
      }
    },
    "bourbaki-tunnel": {
      "command": "/home/ramanujan/anaconda3/bin/python",
      "args": ["/home/ramanujan/PP/funeraria/remote-mcp/start_mcp_server.py"], 
      "cwd": "/home/ramanujan/PP/funeraria/remote-mcp",
      "env": {
        "MCP_SSH_HOST": "127.0.0.1",
        "MCP_SSH_USER": "euler",
        "MCP_SSH_KEY": "/home/ramanujan/.ssh/id_ed25519", 
        "MCP_SSH_PORT": "2222",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
EOF

echo "✅ Enhanced MCP configuration created: $HOME/enhanced_mcp.json"

echo ""
echo "🔧 Phase 5: Create Tunnel Management Scripts"
echo "==========================================="

# Create tunnel status script
cat > "$HOME/check_tunnels.sh" << 'EOF'
#!/bin/bash
echo "🔍 Tunnel Status Report"
echo "======================="

TUNNELS=(
    "FF SSH:127.0.0.1:2223"
    "Bourbaki SSH:127.0.0.1:2222"
    "App Frontend:127.0.0.1:3000"
    "App Backend:127.0.0.1:8080"
    "K8s API:127.0.0.1:6443"
)

for tunnel in "${TUNNELS[@]}"; do
    IFS=':' read -r name listener <<< "$tunnel"
    if netstat -tuln | grep "$listener" > /dev/null; then
        echo "✅ $name - Active"
    else
        echo "❌ $name - Down"
    fi
done
EOF

chmod +x "$HOME/check_tunnels.sh"

# Create tunnel restart script
cat > "$HOME/restart_tunnels.sh" << 'EOF'
#!/bin/bash
echo "🔄 Restarting all tunnels..."

# Kill existing tunnels
pkill -f "cloudflared access tcp" || true
sleep 3

# Restart this setup script
exec "$HOME/PP/funeraria/remote-mcp/setup_network_tunnels.sh"
EOF

chmod +x "$HOME/restart_tunnels.sh"

echo "✅ Management scripts created:"
echo "   - $HOME/check_tunnels.sh (check status)"
echo "   - $HOME/restart_tunnels.sh (restart all)"

echo ""
echo "🎉 Network Setup Complete!"
echo "=========================="
echo ""
echo "📊 Summary:"
echo "  ✅ SSH tunnels for both nodes"
echo "  ✅ Application tunnels ready"
echo "  ✅ Kubernetes API tunnel"
echo "  ✅ Enhanced MCP configuration"
echo "  ✅ Management scripts"
echo ""
echo "🔧 Next Steps:"
echo "  1. Add DNS records in Cloudflare:"
echo "     - ff.buddhilw.com → 179.126.64.212"
echo "     - app.buddhilw.com → 179.126.64.212"
echo "     - api.buddhilw.com → 179.126.64.212"
echo "     - k8s.buddhilw.com → 179.126.64.212"
echo ""
echo "  2. Update Cursor MCP config:"
echo "     cp $HOME/enhanced_mcp.json $HOME/.cursor/mcp.json"
echo ""
echo "  3. Test tunnel status:"
echo "     $HOME/check_tunnels.sh"
echo ""
echo "🚀 Your CGNAT-resistant network is ready!"

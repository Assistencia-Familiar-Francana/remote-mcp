#!/bin/bash
# Setup DuckDNS service on bourbaki node
# This script will be executed on the bourbaki server via SSH

set -euo pipefail

echo "🦆 Setting up DuckDNS service for bourbaki.duckdns.org"
echo "====================================================="

# Configuration
SUBDOMAIN="bourbaki"
TOKEN="a08f5c4f-bd6e-4cda-b09b-7d6d6c95ed47"  # Same token from your DuckDNS account

# Create duckdns directory
echo "📁 Creating duckdns directory..."
mkdir -p ~/duckdns
cd ~/duckdns

# Create the update script
echo "📝 Creating duck.sh script..."
cat > duck.sh << EOF
#!/usr/bin/env bash
set -euo pipefail

# DuckDNS update script for bourbaki subdomain
echo url="https://www.duckdns.org/update?domains=${SUBDOMAIN}&token=${TOKEN}&ip=" | curl -k -o ~/duckdns/duck.log -K -

# Log the result with timestamp
echo "\$(date): DuckDNS update completed" >> ~/duckdns/update.log
EOF

# Make script executable
chmod 700 duck.sh

echo "🧪 Testing DuckDNS update..."
./duck.sh

# Check result
echo "📊 DuckDNS update result:"
if [ -f duck.log ]; then
    cat duck.log
    if grep -q "OK" duck.log; then
        echo "✅ DuckDNS update successful!"
    else
        echo "❌ DuckDNS update failed. Check configuration."
        exit 1
    fi
else
    echo "❌ No log file created. Check network connectivity."
    exit 1
fi

# Create systemd service files
echo "⚙️  Creating systemd service files..."

# Create environment file
sudo tee /etc/duckdns.env > /dev/null << EOF
SUBDOMAIN=${SUBDOMAIN}
TOKEN=${TOKEN}
EOF

# Create systemd service
sudo tee /etc/systemd/system/duckdns.service > /dev/null << 'EOF'
[Unit]
Description=DuckDNS updater for bourbaki

[Service]
Type=oneshot
ExecStart=/home/euler/duckdns/duck.sh
User=euler
Group=euler
EOF

# Create systemd timer
sudo tee /etc/systemd/system/duckdns.timer > /dev/null << 'EOF'
[Unit]
Description=Run DuckDNS updater every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=duckdns.service

[Install]
WantedBy=timers.target
EOF

# Enable and start the timer
echo "🚀 Enabling and starting DuckDNS timer..."
sudo systemctl daemon-reload
sudo systemctl enable duckdns.timer
sudo systemctl start duckdns.timer

# Check status
echo "📊 Service status:"
sudo systemctl status duckdns.timer --no-pager
echo ""
echo "📊 Recent service runs:"
sudo systemctl status duckdns.service --no-pager

echo ""
echo "✅ DuckDNS service setup complete for bourbaki!"
echo "🔄 The service will update bourbaki.duckdns.org every 5 minutes"
echo ""
echo "📝 To check logs:"
echo "   tail -f ~/duckdns/update.log"
echo "   sudo journalctl -u duckdns.service -f"

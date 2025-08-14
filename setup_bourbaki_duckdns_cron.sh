#!/bin/bash
# Setup DuckDNS service on bourbaki node using cron (no sudo required)
# This script will be executed on the bourbaki server via SSH

set -euo pipefail

echo "🦆 Setting up DuckDNS service for bourbaki.duckdns.org (using cron)"
echo "=================================================================="

# Configuration
SUBDOMAIN="bourbaki"
TOKEN="a08f5c4f-bd6e-4cda-b09b-7d6d6c95ed47"

# Create duckdns directory
echo "📁 Creating duckdns directory..."
mkdir -p ~/duckdns
cd ~/duckdns

# Create the update script (improved version)
echo "📝 Creating duck.sh script..."
cat > duck.sh << EOF
#!/usr/bin/env bash
set -euo pipefail

# DuckDNS update script for bourbaki subdomain
LOGFILE=~/duckdns/duck.log
UPDATE_LOG=~/duckdns/update.log

echo url="https://www.duckdns.org/update?domains=${SUBDOMAIN}&token=${TOKEN}&ip=" | curl -k -o "\$LOGFILE" -K -

# Log the result with timestamp
if [ -f "\$LOGFILE" ]; then
    RESULT=\$(cat "\$LOGFILE")
    echo "\$(date): DuckDNS update result: \$RESULT" >> "\$UPDATE_LOG"
    
    if [ "\$RESULT" = "OK" ]; then
        echo "\$(date): ✅ bourbaki.duckdns.org updated successfully" >> "\$UPDATE_LOG"
    else
        echo "\$(date): ❌ bourbaki.duckdns.org update failed: \$RESULT" >> "\$UPDATE_LOG"
    fi
else
    echo "\$(date): ❌ No response from DuckDNS" >> "\$UPDATE_LOG"
fi
EOF

# Make script executable
chmod 700 duck.sh

echo "🧪 Testing DuckDNS update..."
./duck.sh

# Check result
echo "📊 DuckDNS update result:"
if [ -f duck.log ]; then
    RESULT=$(cat duck.log)
    echo "Result: $RESULT"
    if [ "$RESULT" = "OK" ]; then
        echo "✅ DuckDNS update successful!"
    else
        echo "❌ DuckDNS update failed: $RESULT"
        exit 1
    fi
else
    echo "❌ No log file created. Check network connectivity."
    exit 1
fi

# Check if cron is running
echo "🔍 Checking if cron is available..."
if pgrep -x "cron" > /dev/null || pgrep -x "crond" > /dev/null; then
    echo "✅ Cron service is running"
else
    echo "⚠️  Cron service not detected. The timer may not work."
fi

# Add to crontab (update every 5 minutes)
echo "⏰ Adding cron job..."
CRON_JOB="*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "~/duckdns/duck.sh"; then
    echo "⚠️  Cron job already exists, skipping..."
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added successfully"
fi

# Show current crontab
echo "📋 Current crontab:"
crontab -l | grep -E "(duckdns|duck\.sh)" || echo "No DuckDNS cron jobs found"

# Create a status check script
echo "📊 Creating status check script..."
cat > check_status.sh << 'EOF'
#!/bin/bash
echo "🦆 Bourbaki DuckDNS Status"
echo "========================="
echo ""
echo "📊 Last 5 updates:"
if [ -f ~/duckdns/update.log ]; then
    tail -5 ~/duckdns/update.log
else
    echo "No update log found"
fi

echo ""
echo "📋 Active cron jobs:"
crontab -l | grep -E "(duckdns|duck\.sh)" || echo "No DuckDNS cron jobs found"

echo ""
echo "🌐 Current IP (from DuckDNS perspective):"
curl -s https://www.duckdns.org/update?domains=bourbaki&token=a08f5c4f-bd6e-4cda-b09b-7d6d6c95ed47&ip= || echo "Failed to check IP"
EOF

chmod +x check_status.sh

echo ""
echo "✅ DuckDNS service setup complete for bourbaki!"
echo "🔄 The service will update bourbaki.duckdns.org every 5 minutes via cron"
echo ""
echo "📝 Useful commands:"
echo "   ~/duckdns/check_status.sh    # Check service status"
echo "   tail -f ~/duckdns/update.log # Watch live updates"
echo "   ~/duckdns/duck.sh            # Manual update"
echo ""
echo "🧪 Testing manual update in 5 seconds..."
sleep 5
echo "Running manual test..."
./duck.sh
echo ""
echo "📊 Latest update log:"
tail -1 ~/duckdns/update.log 2>/dev/null || echo "No update log yet"

#!/bin/bash

# Temporary fix for bourbaki SSH access
# This script modifies the SSH config to use the working tunnel

echo "Creating temporary SSH config fix..."

# Backup current config
cp ~/.ssh/config ~/.ssh/config.backup.$(date +%Y%m%d_%H%M%S)

# Create a temporary config that uses the working tunnel
cat > ~/.ssh/config.temp << 'EOF'
Host ff
  HostName 100.65.56.110
  User abel
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 8h
  ServerAliveInterval 30
  ServerAliveCountMax 5

Host bourbaki
  HostName 100.68.2.41
  User euler
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 8h
  ServerAliveInterval 30
  ServerAliveCountMax 5

Host home
  HostName ssh.buddhilw.com
  User abel
  ProxyCommand cloudflared access ssh --hostname %h

# Temporary fix: use home tunnel to access bourbaki
Host bourbaki-temp
  HostName 192.168.15.76
  User euler
  ProxyCommand ssh home -W %h:%p

# Original bourbaki config (commented out until tunnel is fixed)
# Host bourbaki
#   HostName bourbaki.buddhilw.com
#   User euler
#   ProxyCommand cloudflared access ssh --hostname %h
EOF

echo "Temporary config created. To use it:"
echo "1. Replace your current config: mv ~/.ssh/config.temp ~/.ssh/config"
echo "2. Connect using: ssh bourbaki-temp"
echo "3. To restore original: mv ~/.ssh/config.backup.* ~/.ssh/config"

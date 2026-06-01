#!/bin/sh

# Append SSH forwarding settings
echo "GatewayPorts yes" | sudo tee -a /etc/ssh/sshd_config
echo "AllowTcpForwarding yes" | sudo tee -a /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd

# Open port 9016 in UFW
sudo ufw allow 9016

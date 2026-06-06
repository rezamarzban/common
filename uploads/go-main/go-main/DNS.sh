#!/bin/SSH

echo "DNS=193.186.32.32" | sudo tee -a /etc/systemd/resolved.conf

sudo systemctl restart systemd-resolved

sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf


sudo tee /etc/apt/sources.list > /dev/null <<'EOF'
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy main restricted
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-updates main restricted
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy universe
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-updates universe
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy multiverse
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-updates multiverse
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-backports main restricted universe multiverse
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-security main restricted
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-security universe
deb https://ir.ubuntu.sindad.cloud/ubuntu jammy-security multiverse
EOF
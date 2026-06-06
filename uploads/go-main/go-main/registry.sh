
sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak 2>/dev/null

sudo tee /etc/docker/daemon.json <<'EOF'
{
  "insecure-registries": ["https://docker.arvancloud.ir"],
  "registry-mirrors": ["https://docker.arvancloud.ir"]
}
EOF

sudo systemctl restart docker

docker run hello-world
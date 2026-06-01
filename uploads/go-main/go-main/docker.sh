
curl -fsSL https://archive.ito.gov.ir/docker-ce/linux/ubuntu/gpg \
 | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://archive.ito.gov.ir/docker-ce/linux/ubuntu jammy stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io

sudo systemctl enable docker

docker --version

sudo usermod -aG docker ubuntu
su ubuntu
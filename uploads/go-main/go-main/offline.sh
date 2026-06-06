#!/usr/bin/env bash
# ------------------------------------------------------------
#  Download the Docker‑related packages listed below
#  with a single xargs –n1 command.
# ------------------------------------------------------------

mkdir -p ~/docker_debs
cd ~/docker_debs

# Make sure the package cache is up‑to‑date
sudo apt-get update

# Download each package (no installation – just the .deb files)
cat <<'EOF' | xargs -n1 apt-get download
docker-buildx-plugin
docker-ce-rootless-extras
docker-compose-plugin
libltdl7
libslirp0
pigz
slirp4netns
aufs-tools
cgroupfs-mount
cgroup-lite
containerd.io
docker-ce
docker-ce-cli
EOF

tar -czf ~/docker_debs.tar.gz -C ~/ docker_debs
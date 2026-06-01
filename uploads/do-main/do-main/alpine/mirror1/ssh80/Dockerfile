# 1️⃣ Pull Alpine from ArvanCloud
FROM docker.arvancloud.ir/library/alpine:latest

# 2️⃣ Install OpenSSH, dumb‑init, generate host keys and set root password
RUN set -eux; \
    apk add --no-cache openssh dumb-init; \
    \
    # Generate host keys – this must be done before sshd starts
    ssh-keygen -A; \
    \
    # Set a sample root password (replace with a strong one!)
    echo "root:Password123!" | chpasswd; \
    \
    # Allow root login by password and change the SSH listening port
    sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config; \
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config; \
    echo "Port 80" >> /etc/ssh/sshd_config; \
    \
    # Clean up package cache
    rm -rf /var/cache/apk/*

# 3️⃣ Expose port 80 (instead of 22)
EXPOSE 80

# 4️⃣ Start the SSH daemon (dumb‑init will forward signals)
CMD ["dumb-init", "--", "/usr/sbin/sshd", "-D"]
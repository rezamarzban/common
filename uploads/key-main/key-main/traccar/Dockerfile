# ========== Stage 1: Build minimal JRE using jlink ==========
FROM eclipse-temurin:21-alpine AS jdk-builder

RUN jlink --module-path $JAVA_HOME/jmods \
    --add-modules java.se,jdk.charsets,jdk.crypto.ec,jdk.unsupported \
    --strip-debug --no-header-files --no-man-pages --compress=2 \
    --output /jre

# ========== Stage 2: Final image with JRE + SSH ==========
FROM alpine:3.23

# Copy the custom JRE from the builder stage
COPY --from=jdk-builder /jre /usr/lib/jvm/jre-21

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/jre-21
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install OpenSSH, dumb-init, and additional tools (adjust as needed)
RUN set -eux; \
    apk add --no-cache \
        openssh \
        dumb-init \
        git \
        nodejs \
        npm \
        python3; \
    \
    # Generate SSH host keys
    ssh-keygen -A; \
    \
    # Set root password (⚠️ Replace with a strong password for production)
    echo "root:Password123!" | chpasswd; \
    \
    # Allow root login via password
    sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config; \
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config; \
    \
    # Enable TCP forwarding (useful for port forwarding scenarios)
    sed -i 's/^AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config; \
    sed -i 's/^GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config; \
    \
    # Clean up package cache to reduce image size
    rm -rf /var/cache/apk/*

# Expose the default SSH port
EXPOSE 22

# Start SSH daemon in foreground using dumb-init
CMD ["dumb-init", "--", "/usr/sbin/sshd", "-D"]
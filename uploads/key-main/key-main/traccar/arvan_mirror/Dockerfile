# ========== Stage 1: Build minimal JRE using jlink ==========
FROM docker.arvancloud.ir/library/eclipse-temurin:21-alpine AS jdk-builder

RUN jlink --module-path $JAVA_HOME/jmods \
    --add-modules java.se,jdk.charsets,jdk.crypto.ec,jdk.unsupported \
    --strip-debug --no-header-files --no-man-pages --compress=2 \
    --output /jre

# ========== Stage 2: Final image with JRE + SSH ==========
FROM docker.arvancloud.ir/library/alpine:3.10

# Copy the custom JRE from the builder stage
COPY --from=jdk-builder /jre /usr/lib/jvm/jre-21

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/jre-21
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# 2️⃣ Switch to ArvanCloud mirrors, install OpenSSH, dumb‑init, generate host keys and set root password
RUN set -eux; \
    # Detect Alpine version and use ArvanCloud mirrors
    ALPINE_VERSION=$(cat /etc/alpine-release | cut -d'.' -f1-2); \
    echo "https://mirror.arvancloud.ir/alpine/v${ALPINE_VERSION}/main" > /etc/apk/repositories; \
    echo "https://mirror.arvancloud.ir/alpine/v${ALPINE_VERSION}/community" >> /etc/apk/repositories; \
    # Install required packages
    apk add --no-cache openssh dumb-init nano curl git python3 py3-flask py3-requests; \
    # Generate host keys – required for sshd to start
    ssh-keygen -A; \
    # Set a sample root password (replace with a strong one!)
    echo "root:Password123!" | chpasswd; \
    # Allow root login by password
    sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config; \
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config; \
    # Clean up package cache
    rm -rf /var/cache/apk/*

# 3️⃣ Expose port 22 (default SSH port)
EXPOSE 22

# 4️⃣ Start the SSH daemon (dumb‑init will forward signals)
CMD ["dumb-init", "--", "/usr/sbin/sshd", "-D"]
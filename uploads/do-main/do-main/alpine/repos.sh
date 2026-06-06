ALPINE_VERSION=$(cat /etc/alpine-release | cut -d'.' -f1-2)
echo "https://mirror.arvancloud.ir/alpine/v${ALPINE_VERSION}/main" > /etc/apk/repositories
echo "https://mirror.arvancloud.ir/alpine/v${ALPINE_VERSION}/community" >> /etc/apk/repositories
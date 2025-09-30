ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system dependencies optimized for multi-architecture
RUN apk add --no-cache \
    python3=~3.11 \
    py3-pip \
    sqlite \
    curl \
    jq \
    git \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    sqlite-dev \
    cargo \
    rust \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /opt/printernizer

# Clone Printernizer from upstream repository
ARG PRINTERNIZER_VERSION="main"
RUN git clone https://github.com/schmacka/printernizer.git /tmp/printernizer \
    && cp -r /tmp/printernizer/src /opt/printernizer/ \
    && cp -r /tmp/printernizer/frontend /opt/printernizer/ \
    && cp /tmp/printernizer/requirements.txt /opt/printernizer/ \
    && rm -rf /tmp/printernizer

# Create requirements file optimized for Home Assistant addon
COPY requirements-addon.txt /opt/printernizer/
RUN cat requirements.txt >> requirements-addon.txt

# Install Python dependencies with ARM optimization
RUN pip3 install --no-cache-dir \
    --extra-index-url https://www.piwheels.org/simple \
    --prefer-binary \
    --find-links https://wheels.home-assistant.io/alpine-3.18/$(apk --print-arch)/ \
    -r requirements-addon.txt \
    && rm -rf /root/.cache/pip

# Copy addon-specific files
COPY rootfs /

# Create application user and directories
RUN addgroup -g 1000 printernizer \
    && adduser -D -s /bin/bash -u 1000 -G printernizer printernizer \
    && mkdir -p /data/downloads /data/logs /data/backups \
    && chown -R printernizer:printernizer /opt/printernizer /data

# Set proper permissions for s6-overlay
RUN chmod a+x /etc/services.d/printernizer/run \
    && chmod a+x /etc/cont-init.d/*.sh

# Configure Python path and environment
ENV PYTHONPATH="/opt/printernizer/src"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Labels for Home Assistant addon
LABEL \
    io.hass.name="Printernizer" \
    io.hass.description="Professional 3D printer management system" \
    io.hass.arch="armhf|aarch64|amd64" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    io.hass.base.name="Home Assistant base Python image" \
    io.hass.base.version="3.11-alpine3.18" \
    maintainer="Sebastian Kristof <sebastiankristof@gmail.com>" \
    org.opencontainers.image.title="Printernizer Home Assistant Addon" \
    org.opencontainers.image.description="Professional 3D printer management for Bambu Lab and Prusa printers" \
    org.opencontainers.image.source="https://github.com/schmacka/printernizer-ha" \
    org.opencontainers.image.licenses="AGPL-3.0" \
    org.opencontainers.image.documentation="https://github.com/schmacka/printernizer-ha/blob/main/README.md"

# Expose port (internal only, ingress handles external access)
EXPOSE 8000

# Default command handled by s6-overlay
CMD []
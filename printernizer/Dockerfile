# Printernizer - Home Assistant Add-on
# Multi-architecture support with optimized multi-stage build

# ============================================
# Stage 1: Builder - Compile dependencies
# ============================================
ARG BUILD_FROM
FROM ${BUILD_FROM} as builder

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Detect architecture for conditional package installation
RUN arch=$(uname -m) && echo "Building for architecture: $arch" && \
    echo "Platform: $(uname -a)"

# Install build dependencies and architecture-specific packages
# For armv7, use Alpine system packages where available to avoid Rust compilation
RUN apk update && \
    if [ "$(uname -m)" = "armv7l" ]; then \
        echo "Installing armv7-specific Alpine packages to avoid Rust compilation..." && \
        apk add --no-cache \
            gcc g++ gfortran musl-dev python3-dev libffi-dev \
            py3-pip py3-setuptools py3-wheel \
            py3-numpy py3-scipy py3-matplotlib py3-pillow \
            py3-cryptography \
            openblas-dev lapack-dev && \
        rm -rf /var/cache/apk/*; \
    else \
        apk add --no-cache \
            gcc g++ gfortran musl-dev python3-dev libffi-dev \
            openblas-dev lapack-dev py3-pip && \
        rm -rf /var/cache/apk/*; \
    fi

# Copy requirements first for better layer caching
COPY requirements.txt /tmp/

# Install Python packages with aggressive wheel preference for ARM
# For armv7: Use ONLY pre-built wheels to avoid Rust compilation issues
# Alpine packages installed above will satisfy some requirements (numpy, scipy, etc.)
# We MUST avoid compiling packages with Rust dependencies as rustup doesn't support arm-unknown-linux-musleabihf
# Note: pip will skip packages already satisfied by Alpine system packages
RUN if [ "$(uname -m)" = "armv7l" ]; then \
        echo "Installing packages for armv7 - using piwheels as primary source..." && \
        pip3 install --no-cache-dir --user --break-system-packages \
            --only-binary=:all: \
            --index-url https://www.piwheels.org/simple \
            --extra-index-url https://pypi.org/simple \
            --trusted-host www.piwheels.org \
            --default-timeout=300 \
            -r /tmp/requirements.txt; \
    else \
        pip3 install --no-cache-dir --user --break-system-packages \
            --prefer-binary \
            --only-binary=:all: \
            --extra-index-url https://www.piwheels.org/simple \
            --trusted-host www.piwheels.org \
            --default-timeout=300 \
            -r /tmp/requirements.txt || \
        pip3 install --no-cache-dir --user --break-system-packages \
            --prefer-binary \
            --extra-index-url https://www.piwheels.org/simple \
            -r /tmp/requirements.txt; \
    fi

# ============================================
# Stage 2: Runtime - Lean production image
# ============================================
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set environment variables
ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEPLOYMENT_MODE=homeassistant \
    HA_INGRESS=true \
    PATH=/root/.local/bin:$PATH

# Install runtime dependencies (no build tools)
# For armv7, include Alpine packages to avoid runtime issues
RUN apk update && \
    if [ "$(uname -m)" = "armv7l" ]; then \
        echo "Installing armv7-specific runtime packages..." && \
        apk add --no-cache \
            python3 py3-pip py3-brotli py3-setuptools py3-wheel \
            py3-numpy py3-scipy py3-matplotlib py3-pillow \
            py3-cryptography \
            sqlite curl jq bash tzdata \
            openblas lapack libgfortran libstdc++ && \
        rm -rf /var/cache/apk/*; \
    else \
        apk add --no-cache \
            python3 py3-pip py3-brotli \
            sqlite curl jq bash tzdata \
            openblas lapack libgfortran libstdc++ && \
        rm -rf /var/cache/apk/*; \
    fi

# Copy compiled Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy application files
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY database_schema.sql /app/

# Copy Home Assistant specific files
COPY run.sh /
RUN chmod +x /run.sh

# Create necessary directories
RUN mkdir -p /data \
    /app/logs \
    /app/temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port for Home Assistant Ingress
EXPOSE 8000

# Labels for Home Assistant
LABEL io.hass.name="Printernizer" \
      io.hass.description="Professional 3D Printer Management System" \
      io.hass.type="addon" \
      io.hass.version="2.9.5" \
      io.hass.arch="aarch64|amd64|armv7"

# Start the add-on service
CMD ["/run.sh"]

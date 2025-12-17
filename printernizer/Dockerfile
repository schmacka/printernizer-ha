# Printernizer - Home Assistant Add-on
# Multi-architecture support with optimized multi-stage build

# ============================================
# Stage 1: Builder - Compile dependencies
# ============================================
ARG BUILD_FROM
FROM ${BUILD_FROM} as builder

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install build dependencies with --no-scripts to avoid QEMU overhead
RUN apk add --no-cache --no-scripts \
    gcc \
    g++ \
    gfortran \
    musl-dev \
    python3-dev \
    libffi-dev \
    openblas-dev \
    lapack-dev \
    py3-pip \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better layer caching
COPY requirements.txt /tmp/

# Install Python packages in user directory
RUN pip3 install --no-cache-dir --user --break-system-packages -r /tmp/requirements.txt

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

# Install ONLY runtime dependencies (no build tools)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-brotli \
    sqlite \
    curl \
    jq \
    bash \
    tzdata \
    && rm -rf /var/cache/apk/*

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
      io.hass.arch="aarch64|amd64|armv7|armhf"

# Start the add-on service
CMD ["/run.sh"]

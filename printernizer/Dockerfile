# Printernizer - Home Assistant Add-on
# Debian (glibc) base. The model generator runs in the browser (JSCAD), so the
# server has no CAD dependency. Debian remains only so the optional matplotlib
# STL/3MF preview thumbnails have prebuilt wheels. Builds on amd64, aarch64, armv7.

# ============================================
# Stage 1: Builder - Compile dependencies
# ============================================
ARG BUILD_FROM
FROM ${BUILD_FROM} as builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN echo "Building for architecture: $(uname -m)" && echo "Platform: $(uname -a)"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev \
        gcc \
        g++ \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt /tmp/

# Install Python packages from requirements.txt.
# Prefer pre-built binary wheels; fall back to source only if needed.
# piwheels provides ARM wheels (arm64/armhf) for packages without official ones.
# matplotlib is NOT in requirements.txt (no musl wheel) but works on Debian, so
# it is installed here as an optional extra (STL/3MF preview thumbnails).
RUN pip3 install --no-cache-dir --user --break-system-packages \
        --prefer-binary \
        --extra-index-url https://www.piwheels.org/simple \
        --trusted-host www.piwheels.org \
        --default-timeout=300 \
        -r /tmp/requirements.txt

# Optional: matplotlib (STL/3MF preview thumbnails). Best-effort and via piwheels
# so armv7 can use a prebuilt wheel; on any arch without a wheel it would build
# from source (needs freetype + patch/git), so failures are non-fatal and preview
# rendering simply degrades gracefully.
# --ignore-installed forces matplotlib's FULL dependency tree (packaging,
# pyparsing, python-dateutil, etc.) into /root/.local. Without it, deps already
# satisfied by a system package in the builder are skipped and never copied to
# the final stage (COPY --from=builder /root/.local), so matplotlib fails to
# import at runtime ("No module named 'packaging'") and STL previews silently break.
RUN pip3 install --no-cache-dir --user --break-system-packages \
        --ignore-installed \
        --prefer-binary \
        --extra-index-url https://www.piwheels.org/simple \
        --trusted-host www.piwheels.org \
        --default-timeout=300 \
        matplotlib \
    || echo "matplotlib not installable on this architecture; STL preview rendering disabled"

# NOTE: the model generator no longer has a server-side dependency — geometry is
# generated in the browser (JSCAD). No build123d / OpenCascade install is needed,
# which is what makes the generator work on aarch64/armv7 too.

# ============================================
# Stage 2: Runtime - Lean production image
# ============================================
FROM ${BUILD_FROM}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEPLOYMENT_MODE=homeassistant \
    HA_INGRESS=true \
    PATH=/root/.local/bin:$PATH

# Install runtime dependencies. No CAD/GL libs needed — the model generator runs
# in the browser. libopenblas0/libgfortran5 back numpy/scipy; fonts-dejavu-core
# backs matplotlib's STL/3MF preview thumbnails.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        sqlite3 \
        curl \
        jq \
        tzdata \
        ffmpeg \
        fonts-dejavu-core \
        ca-certificates \
        libopenblas0 \
        libgfortran5 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy application files
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY database_schema.sql /app/
COPY migrations/ /app/migrations/

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

# Printernizer - Home Assistant Add-on
# Debian (glibc) base. Required by the build123d model generator: it depends on
# OpenCascade via the OCP bindings, which ship manylinux (glibc) wheels only
# (no musllinux build), so an Alpine base is not an option. matplotlib STL/3MF
# previews also work here (no musl/aarch64 wheel constraint). All on amd64,
# aarch64 and armv7.

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
# matplotlib and build123d are NOT in requirements.txt (excluded upstream for
# musl/armv7 wheel compatibility) but work on Debian/glibc, so they are installed
# here as optional extras.
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
RUN pip3 install --no-cache-dir --user --break-system-packages \
        --prefer-binary \
        --extra-index-url https://www.piwheels.org/simple \
        --trusted-host www.piwheels.org \
        --default-timeout=300 \
        matplotlib \
    || echo "matplotlib not installable on this architecture; STL preview rendering disabled"

# Optional: build123d (parametric model generator). cadquery-ocp wheel coverage
# is split by architecture, so the install differs per arch (all best-effort —
# the generator degrades gracefully when build123d is absent):
#   x86_64  : build123d 0.10.0 + its pinned cadquery-ocp 7.8.x (proven path).
#   aarch64 : 7.8.x has NO linux-arm64 wheel; the only arm64 OCP wheel is
#             cadquery-ocp 7.9.3.x, which build123d 0.10.0 pins out. So we mix
#             versions: build123d (--no-deps) on top of the OCP 7.9 world
#             (cadquery-ocp 7.9.3 + ocpsvg 0.6 + ocp_gordon 0.2). EXPERIMENTAL.
#   armv7   : no OCP wheel at all → skipped.
RUN ARCH="$(uname -m)"; \
    if [ "$ARCH" = "x86_64" ]; then \
        pip3 install --no-cache-dir --user --break-system-packages \
            --prefer-binary --default-timeout=300 "build123d>=0.9.1" \
        || echo "build123d not installable; model generator disabled"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        echo "aarch64: installing build123d with cadquery-ocp 7.9.3 (experimental)"; \
        pip3 install --no-cache-dir --user --break-system-packages \
            --prefer-binary --default-timeout=300 \
            "cadquery-ocp==7.9.3.1.1" "ocpsvg>=0.6" "ocp_gordon>=0.2" \
            typing_extensions svgpathtools anytree ezdxf ipython "lib3mf>=2.4.1" \
            trianglesolver sympy webcolors \
        && pip3 install --no-cache-dir --user --break-system-packages \
            --no-deps "build123d==0.10.0" \
        || echo "build123d (arm64 OCP 7.9 override) failed; model generator disabled"; \
    else \
        echo "$ARCH: no cadquery-ocp wheel; model generator disabled"; \
    fi

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

# Install runtime dependencies.
# libgl1/libglu1-mesa/libxrender1/libxext6/libsm6/libgomp1/fontconfig are
# required by OpenCascade/OCP (the build123d model generator). No external
# CAD binary is needed — build123d renders geometry in-process.
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
        libgl1 \
        libglu1-mesa \
        libxrender1 \
        libxext6 \
        libsm6 \
        libgomp1 \
        fontconfig \
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

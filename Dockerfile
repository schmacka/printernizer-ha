ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.0.1
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk update && \
    apk add --no-cache \
        python3 \
        py3-pip \
        curl \
    && apk add --no-cache --virtual .build-deps \
        git \
        gcc \
        musl-dev \
        linux-headers \
        python3-dev

# Create app directory
WORKDIR /app

# Clone the upstream Printernizer repository
RUN git clone https://github.com/schmacka/printernizer.git .

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    aiosqlite \
    aiohttp \
    websockets \
    pydantic \
    paho-mqtt \
    python-dotenv \
    aiofiles \
    && apk del .build-deps

# Create s6-overlay service directory
RUN mkdir -p /etc/services.d/printernizer

# Create s6-overlay service run script
RUN echo '#!/usr/bin/with-contenv bashio\n\
# ==============================================================================\n\
# Start the Printernizer service\n\
# s6-overlay docs: https://github.com/just-containers/s6-overlay\n\
# ==============================================================================\n\
\n\
bashio::log.info "Starting Printernizer..."\n\
\n\
# Set up environment variables from Home Assistant options\n\
export PORT=8000\n\
export HOST=0.0.0.0\n\
export DATABASE_URL=sqlite:////config/printernizer.db\n\
\n\
# Create config directory if it does not exist\n\
mkdir -p /config\n\
\n\
cd /app\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info' > /etc/services.d/printernizer/run

# Make the run script executable
RUN chmod a+x /etc/services.d/printernizer/run

# Create s6-overlay service finish script (optional, for cleanup)
RUN echo '#!/usr/bin/with-contenv bashio\n\
# ==============================================================================\n\
# Take down the S6 supervision tree when the service fails\n\
# s6-overlay docs: https://github.com/just-containers/s6-overlay\n\
# ==============================================================================\n\
\n\
if [[ "$1" -ne 0 ]] && [[ "$1" -ne 256 ]]; then\n\
  bashio::log.info "Printernizer crashed with exit code $1"\n\
  bashio::log.info "Shutting down s6-overlay..."\n\
  /run/s6/basedir/bin/halt\n\
fi' > /etc/services.d/printernizer/finish

# Make the finish script executable
RUN chmod a+x /etc/services.d/printernizer/finish

# Expose web port
EXPOSE 8000

# Health check for Home Assistant
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

# Labels for Home Assistant addon
LABEL \
    io.hass.name="Printernizer" \
    io.hass.description="3D Printer Management for Home Assistant" \
    io.hass.arch="armhf|armv7|aarch64|i386|amd64" \
    io.hass.type="addon" \
    io.hass.version="0.0.10"

# Let s6-overlay handle the init process (PID 1)
# The s6-overlay will automatically start services defined in /etc/services.d/
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache nodejs npm curl

# Create app directory
WORKDIR /app

# Create a minimal package.json since upstream repo is empty
RUN echo '{\
  "name": "printernizer",\
  "version": "1.0.0",\
  "description": "Printernizer 3D Printer Management",\
  "main": "index.js",\
  "scripts": {\
    "start": "node index.js"\
  },\
  "dependencies": {\
    "express": "^4.18.2"\
  }\
}' > package.json

# Install npm dependencies
RUN npm install

# Create a minimal Express server as placeholder
RUN echo 'const express = require("express");\
const app = express();\
const port = process.env.PORT || 8080;\
\
app.get("/", (req, res) => {\
  res.send(`\
    <html>\
      <head><title>Printernizer</title></head>\
      <body>\
        <h1>Printernizer 3D Printer Management</h1>\
        <p>Welcome to Printernizer - your 3D printer management system.</p>\
        <p>This addon is currently in development. The upstream repository is not yet ready.</p>\
        <p>Check <a href="https://github.com/schmacka/printernizer">github.com/schmacka/printernizer</a> for updates.</p>\
      </body>\
    </html>\
  `);\
});\
\
app.listen(port, "0.0.0.0", () => {\
  console.log(`Printernizer listening on port ${port}`);\
});' > index.js

# Create s6-overlay service directory
RUN mkdir -p /etc/services.d/printernizer

# Create s6-overlay service run script
RUN echo '#!/usr/bin/with-contenv bashio\
# ==============================================================================\
# Start the Printernizer service\
# s6-overlay docs: https://github.com/just-containers/s6-overlay\
# ==============================================================================\
\
bashio::log.info "Starting Printernizer..."\
\
cd /app\
exec npm start' > /etc/services.d/printernizer/run

# Make the run script executable
RUN chmod a+x /etc/services.d/printernizer/run

# Create s6-overlay service finish script (optional, for cleanup)
RUN echo '#!/usr/bin/with-contenv bashio\
# ==============================================================================\
# Take down the S6 supervision tree when the service fails\
# s6-overlay docs: https://github.com/just-containers/s6-overlay\
# ==============================================================================\
\
if [[ "$1" -ne 0 ]] && [[ "$1" -ne 256 ]]; then\
  bashio::log.info "Printernizer crashed with exit code $1"\
  bashio::log.info "Shutting down s6-overlay..."\
  /run/s6/basedir/bin/halt\
fi' > /etc/services.d/printernizer/finish

# Make the finish script executable
RUN chmod a+x /etc/services.d/printernizer/finish

# Expose web port
EXPOSE 8080

# Health check for Home Assistant
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s \
  CMD curl --fail http://localhost:8080 || exit 1

# Labels for Home Assistant addon
LABEL \
    io.hass.name="Printernizer" \
    io.hass.description="3D Printer Management for Home Assistant" \
    io.hass.arch="armhf|aarch64|i386|amd64" \
    io.hass.type="addon" \
    io.hass.version="0.0.5"

# Let s6-overlay handle the init process (PID 1)
# The s6-overlay will automatically start services defined in /etc/services.d/

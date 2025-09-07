ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache nodejs npm

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

# Expose web port
EXPOSE 8080

# Start the application
CMD ["npm", "start"]

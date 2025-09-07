ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache git nodejs npm

# Clone Printernizer
WORKDIR /opt
RUN git clone https://github.com/schmacka/printernizer.git

WORKDIR /opt/printernizer

# Install npm dependencies
RUN npm install

# Expose web port
EXPOSE 8080

# Start Printernizer
CMD ["npm", "start"]

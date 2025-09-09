#!/bin/bash

# Build and test script for Printernizer Home Assistant addon
# This script helps validate the s6-overlay fix

set -e

echo "🔧 Building Printernizer addon container..."

# Build the container
docker build -t printernizer-ha:test .

echo "✅ Container built successfully!"

echo "🚀 Starting container to test s6-overlay..."

# Run the container in detached mode
CONTAINER_ID=$(docker run -d -p 8080:8080 printernizer-ha:test)

echo "📋 Container ID: $CONTAINER_ID"

# Wait for container to start
echo "⏳ Waiting for container to initialize..."
sleep 10

# Check if s6-overlay is running as PID 1
echo "🔍 Checking if s6-overlay is running as PID 1..."
docker exec $CONTAINER_ID ps aux | head -10

# Check container logs
echo "📝 Container logs:"
docker logs $CONTAINER_ID

# Test if the service is responding
echo "🌐 Testing web service..."
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Web service is responding!"
else
    echo "❌ Web service is not responding"
fi

# Check specific s6-overlay processes
echo "🔍 Checking s6-overlay processes..."
docker exec $CONTAINER_ID pgrep -f s6 || echo "No s6 processes found"

# Cleanup
echo "🧹 Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "🎉 Test completed!"
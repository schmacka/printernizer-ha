#!/bin/bash
# ==============================================================================
# Printernizer Home Assistant Addon - Local Development Script
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ADDON_NAME="printernizer-ha"
LOCAL_TAG="local/${ADDON_NAME}"
TEST_DATA_DIR="./test-data"
BUILD_ARCH="${1:-amd64}"

echo -e "${BLUE}🏗️  Printernizer HA Addon - Development Environment${NC}"
echo -e "${BLUE}Architecture: ${BUILD_ARCH}${NC}"
echo "=============================================================="

# Create test data directory
if [ ! -d "${TEST_DATA_DIR}" ]; then
    echo -e "${YELLOW}📁 Creating test data directory...${NC}"
    mkdir -p "${TEST_DATA_DIR}"
fi

# Build the addon
echo -e "${YELLOW}🔨 Building addon for ${BUILD_ARCH}...${NC}"
docker build \
    --build-arg BUILD_FROM="ghcr.io/home-assistant/base-python:3.11-alpine3.18" \
    --platform "linux/${BUILD_ARCH}" \
    -t "${LOCAL_TAG}:${BUILD_ARCH}" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Function to test the addon
test_addon() {
    echo -e "${YELLOW}🧪 Testing addon startup...${NC}"
    
    # Start container in background
    docker run --rm -d \
        --name "test-${ADDON_NAME}" \
        --platform "linux/${BUILD_ARCH}" \
        -v "$(pwd)/${TEST_DATA_DIR}:/data" \
        -e SUPERVISOR_TOKEN="test-token-$(date +%s)" \
        -e LOG_LEVEL="DEBUG" \
        -p 8000:8000 \
        "${LOCAL_TAG}:${BUILD_ARCH}"
    
    # Wait for startup
    echo -e "${BLUE}⏳ Waiting for addon to start (30s)...${NC}"
    sleep 30
    
    # Test health endpoint
    echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
    if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        
        # Show some basic info
        echo -e "${BLUE}📊 Addon status:${NC}"
        curl -s http://localhost:8000/api/v1/health | jq . || echo "Health endpoint responded"
    else
        echo -e "${RED}❌ Health check failed!${NC}"
        echo -e "${YELLOW}📋 Container logs:${NC}"
        docker logs "test-${ADDON_NAME}" --tail 50
        return 1
    fi
    
    # Cleanup
    echo -e "${YELLOW}🧹 Cleaning up test container...${NC}"
    docker stop "test-${ADDON_NAME}" > /dev/null 2>&1 || true
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}📋 Recent container logs:${NC}"
    docker logs "test-${ADDON_NAME}" --tail 50 2>/dev/null || echo "No container running"
}

# Function to run interactive shell
run_shell() {
    echo -e "${YELLOW}🐚 Starting interactive shell in addon container...${NC}"
    docker run --rm -it \
        --platform "linux/${BUILD_ARCH}" \
        -v "$(pwd)/${TEST_DATA_DIR}:/data" \
        -e SUPERVISOR_TOKEN="dev-token" \
        -e LOG_LEVEL="DEBUG" \
        --entrypoint /bin/bash \
        "${LOCAL_TAG}:${BUILD_ARCH}"
}

# Main menu
case "${2:-test}" in
    "test")
        test_addon
        ;;
    "logs")
        show_logs
        ;;
    "shell")
        run_shell
        ;;
    "build-only")
        echo -e "${GREEN}✅ Build completed. Use './dev.sh ${BUILD_ARCH} test' to test.${NC}"
        ;;
    *)
        echo -e "${BLUE}Usage: $0 [architecture] [command]${NC}"
        echo ""
        echo -e "${YELLOW}Architectures:${NC} amd64, armv7, aarch64"
        echo -e "${YELLOW}Commands:${NC}"
        echo "  test       - Build and test the addon (default)"
        echo "  build-only - Build without testing"
        echo "  shell      - Run interactive shell in container"
        echo "  logs       - Show recent container logs"
        echo ""
        echo -e "${BLUE}Examples:${NC}"
        echo "  $0                    # Build and test amd64"
        echo "  $0 armv7 test         # Build and test armv7"
        echo "  $0 aarch64 shell      # Build aarch64 and run shell"
        ;;
esac
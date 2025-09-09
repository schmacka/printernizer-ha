# Printernizer Integration Plan

## Overview
This document outlines the plan to properly integrate the upstream [Printernizer](https://github.com/schmacka/printernizer) project into this Home Assistant addon.

## Current State Analysis

### Issues with Current Implementation
- **Technology Mismatch**: Current Dockerfile uses Node.js/Express, but Printernizer is Python FastAPI
- **Port Mismatch**: Using port 8080, but Printernizer uses port 8000
- **Placeholder Code**: Contains minimal Express server instead of actual Printernizer
- **Missing Dependencies**: No Python dependencies or proper build process

### Current Configuration
- Home Assistant addon structure correctly set up
- Multi-architecture support (amd64, armv7, aarch64) configured
- Ingress routing configured
- Repository metadata in place

## Upstream Printernizer Analysis

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite
- **Frontend**: Static HTML/JavaScript
- **WebSocket**: Real-time printer communication
- **Protocols**: MQTT and HTTP printer integrations

### Key Dependencies
```
Core Python packages:
- fastapi
- uvicorn[standard] (ASGI server)
- aiosqlite (async SQLite)
- aiohttp (HTTP client)
- websockets
- pydantic (data validation)
- paho-mqtt (MQTT client)
- python-dotenv (environment config)
- aiofiles (async file operations)
```

### Supported Printers
- Bambu Lab A1
- Prusa Core One
- Generic MQTT/HTTP printers

## Integration Strategy

### 1. Dockerfile Rewrite
**Current**: Node.js base → **Target**: Python 3.11+ base

```dockerfile
# Change from Node.js to Python base
FROM ghcr.io/home-assistant/aarch64-base-python:latest

# Install system dependencies
RUN apk add --no-cache git curl

# Clone upstream Printernizer
WORKDIR /app
RUN git clone https://github.com/schmacka/printernizer.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Configure for Home Assistant
COPY run.sh /
RUN chmod a+x /run.sh

CMD ["/run.sh"]
```

### 2. Port Configuration Update
- **Change**: 8080 → 8000 (FastAPI default)
- **Update**: `config.json` ports and ingress_port
- **Update**: Health check URLs

### 3. Environment Configuration
**Home Assistant Options Schema**:
```json
{
  "printers": {
    "bambu_printers": [
      {
        "name": "string",
        "ip": "string", 
        "access_code": "string"
      }
    ],
    "prusa_printers": [
      {
        "name": "string",
        "ip": "string",
        "api_key": "string"
      }
    ]
  },
  "timezone": "Europe/Berlin",
  "vat_rate": 0.19
}
```

### 4. Data Persistence
- **SQLite Database**: Map to `/config/printernizer.db`
- **Configuration**: Use Home Assistant addon options
- **Logs**: Standard Home Assistant logging

### 5. Home Assistant Integration Points
- **Ingress**: Configure CORS for Home Assistant domain
- **Options**: Environment variables from addon configuration
- **Health Check**: FastAPI health endpoint
- **Startup**: s6-overlay service management

## Implementation Steps

### Phase 1: Core Integration
1. ✅ Analyze current state and upstream project
2. ✅ Document integration plan  
3. 🔄 Rewrite Dockerfile for Python/FastAPI
4. ⏳ Update config.json with correct ports and options
5. ⏳ Create startup scripts for Home Assistant

### Phase 2: Configuration
1. ⏳ Add Home Assistant options schema
2. ⏳ Environment variable mapping
3. ⏳ Database persistence setup
4. ⏳ CORS configuration for ingress

### Phase 3: Testing & Polish
1. ⏳ Multi-architecture build testing
2. ⏳ Printer connection testing
3. ⏳ Home Assistant ingress testing
4. ⏳ Documentation updates

## Expected Outcomes

### User Experience
- Access Printernizer through Home Assistant sidebar
- Configure printers via addon options
- Persistent printer data and job history
- Real-time printer status updates

### Technical Benefits  
- Proper Python FastAPI implementation
- SQLite database for printer data
- WebSocket real-time updates
- MQTT/HTTP printer protocol support
- Multi-architecture Docker support

## Risk Mitigation

### Potential Issues
1. **Upstream Changes**: Printernizer is in active development
   - *Mitigation*: Pin to specific commit/tag for stability

2. **Architecture Compatibility**: ARM/x86 builds
   - *Mitigation*: Test on all supported architectures

3. **Home Assistant Integration**: Ingress/CORS issues
   - *Mitigation*: Follow Home Assistant addon best practices

4. **Database Migration**: Existing users (none currently)
   - *Mitigation*: Fresh start acceptable for v0.0.6

## Version Strategy
- Current: v0.0.5 (placeholder implementation)
- Target: v0.0.6 (proper Printernizer integration)
- Use semantic versioning: Major.Minor.Bugfix

---
*Generated: 2025-09-09*
*Status: Planning Complete - Implementation In Progress*
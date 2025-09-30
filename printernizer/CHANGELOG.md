# Changelog

All notable changes to this add-on will be documented in this file.

## [1.1.0] - 2025-09-30

### Added - Phase 2: Integration & Configuration
- Complete Home Assistant Supervisor API integration with authentication
- Enhanced MQTT discovery with comprehensive device registration 
- Full data management system with backup and restore functionality
- Ingress proxy support with proper header handling and security
- Notification system integration with Home Assistant persistent notifications
- Enhanced API v1 endpoints for all addon functionality
- Comprehensive integration test suite for validation
- Professional logging system with rotation and management
- SQLite database with proper schema and migration support
- Backup system with automatic cleanup and metadata

### Enhanced
- Configuration system supporting all addon options from config.yaml
- Web interface with dynamic content and proper templating
- CORS handling and security headers for production deployment
- Error handling and validation across all components
- Async/await patterns for optimal performance

## [1.0.0] - 2025-09-30

### Added
- Initial release of Printernizer Home Assistant Add-on
- Support for Bambu Lab A1 printers via MQTT
- Support for Prusa Core One printers via HTTP API
- Real-time printer status monitoring
- Temperature sensors for bed and hotend
- Print progress tracking
- MQTT discovery for automatic Home Assistant integration
- Responsive web interface accessible through Home Assistant
- Multi-architecture support (amd64, armv7, aarch64)
- Comprehensive configuration options
- Professional logging and error handling

### Features
- **Multi-printer management**: Configure multiple printers of different types
- **Live monitoring**: Real-time status updates and temperature readings
- **Home Assistant integration**: Automatic entity creation via MQTT discovery
- **Mobile responsive**: Optimized web interface for all devices
- **ARM optimization**: Efficient operation on Raspberry Pi devices
- **Secure operation**: Runs with restricted privileges for security

### Technical
- FastAPI-based web application
- Asynchronous printer communication
- SQLite database for persistence
- s6-overlay process management
- Docker multi-stage builds for optimization
- Comprehensive error handling and reconnection logic
# Changelog

All notable changes to this add-on will be documented in this file.

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
# Changelog

All notable changes to the Printernizer Home Assistant Addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial Home Assistant addon implementation
- Multi-architecture support (amd64, armv7, aarch64)
- Ingress web interface integration
- MQTT device discovery for Home Assistant
- Automatic printer status monitoring
- File management and download capabilities
- Home Assistant notification integration
- German business features with VAT support
- Comprehensive configuration options
- Health monitoring and status reporting
- Optimizations for Raspberry Pi deployment

### Technical
- Based on Printernizer v1.0.2
- Uses Home Assistant base Python 3.11 Alpine images
- s6-overlay for proper service management
- Persistent data storage in /data volume
- Multi-stage Docker build process
- Automated CI/CD pipeline with GitHub Actions
- Security scanning with Trivy
- Comprehensive error handling and logging

## [1.0.0] - TBD

### Added
- Initial release of Printernizer Home Assistant Addon
- Full integration with upstream Printernizer project
- Production-ready deployment for home users
- Support for Bambu Lab A1 and Prusa Core One printers
- Mobile-responsive web interface
- Real-time WebSocket updates
- Business analytics and reporting
- Multi-language support (German/English)

### Supported Architectures
- AMD64 (Intel/AMD 64-bit)
- ARMv7 (Raspberry Pi 32-bit)
- AArch64 (Raspberry Pi 64-bit)

### Requirements
- Home Assistant 2023.10.0 or newer
- 2GB+ available storage
- Network access to 3D printers
- Mosquitto broker (optional, for MQTT discovery)

---

**Note**: This changelog tracks the Home Assistant addon specifically. For upstream Printernizer changes, see the [main project changelog](https://github.com/schmacka/printernizer/blob/main/CHANGELOG.md).
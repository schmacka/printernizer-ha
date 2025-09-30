# Printernizer Home Assistant Addon

[![Build Status](https://github.com/schmacka/printernizer-ha/workflows/Build%20Printernizer%20Home%20Assistant%20Addon/badge.svg)](https://github.com/schmacka/printernizer-ha/actions)
[![GitHub Release](https://img.shields.io/github/release/schmacka/printernizer-ha.svg)](https://github.com/schmacka/printernizer-ha/releases)
[![License](https://img.shields.io/github/license/schmacka/printernizer-ha.svg)](LICENSE)

Professional 3D printer management system as a Home Assistant addon. Monitor and manage your Bambu Lab A1 and Prusa Core One printers directly from Home Assistant with full ingress support and MQTT device discovery.

## About

This addon packages the [Printernizer](https://github.com/schmacka/printernizer) 3D printer management system for seamless integration with Home Assistant. It provides comprehensive printer monitoring, job tracking, and file management capabilities optimized for Raspberry Pi deployment.

## Features

- 🖨️ **Multi-Printer Support**: Bambu Lab A1 (MQTT) and Prusa Core One (HTTP API)
- 📊 **Real-time Monitoring**: Live printer status, job progress, and temperatures
- 📁 **File Management**: Automatic file discovery and download system
- 🏠 **Home Assistant Integration**: Ingress web interface and MQTT device discovery
- 📱 **Mobile Responsive**: Optimized interface for phones and tablets
- 🔔 **Notifications**: Integration with Home Assistant notification system
- 📈 **Analytics**: Business reporting with German VAT support
- 🌍 **Multi-Architecture**: Supports AMD64, ARMv7, and AArch64 (Raspberry Pi)

## Installation

### Via Home Assistant Community Store (HACS)

1. **Add Repository**: In HACS, go to "Integrations" → "..." → "Custom repositories"
2. **URL**: `https://github.com/schmacka/printernizer-ha`
3. **Category**: "Add-on"
4. **Install**: Search for "Printernizer" and install

### Manual Installation

1. **Clone Repository**: Add this repository to your Home Assistant addons directory
2. **Refresh**: Reload the addon store in Home Assistant
3. **Install**: Find "Printernizer" in the local addons and install

## Configuration

### Basic Setup

```yaml
log_level: info
timezone: Europe/Berlin
currency: EUR
vat_rate: 19.0
enable_mqtt_discovery: true
printer_polling_interval: 30
printers:
  - name: "Bambu Lab A1 #1"
    type: bambu_lab
    ip_address: "192.168.1.100"
    access_code: "12345678"
    serial_number: "01S00A3B0300123"
    enabled: true
  - name: "Prusa Core One #1"
    type: prusa_core
    ip_address: "192.168.1.101"
    api_key: "your-prusa-api-key"
    enabled: true
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | list | `info` | Logging level (trace, debug, info, warning, error, fatal) |
| `database_path` | string | `/data/printernizer.db` | SQLite database location |
| `downloads_path` | string | `/data/downloads` | File download directory |
| `timezone` | string | `Europe/Berlin` | System timezone |
| `currency` | string | `EUR` | Currency for business features |
| `vat_rate` | float | `19.0` | VAT percentage for invoicing |
| `enable_mqtt_discovery` | bool | `true` | Enable device discovery in HA |
| `mqtt_prefix` | string | `homeassistant` | MQTT discovery prefix |
| `printer_polling_interval` | int | `30` | Status polling interval (seconds) |
| `max_concurrent_downloads` | int | `5` | Maximum parallel downloads |
| `enable_notifications` | bool | `true` | HA notification integration |

### Printer Configuration

#### Bambu Lab A1
- **IP Address**: Printer's network IP address
- **Access Code**: 8-digit code from printer display (Settings → Network → Access Code)
- **Serial Number**: Printer serial number (Settings → About)

#### Prusa Core One
- **IP Address**: Printer's network IP address  
- **API Key**: PrusaLink API key (Settings → API Key)

## Usage

### Web Interface

Access the Printernizer interface through:
- **Home Assistant**: Settings → Add-ons → Printernizer → "Open Web UI"
- **Sidebar**: The Printernizer panel (if enabled)
- **Ingress**: Automatically configured for secure access

### MQTT Discovery

When enabled, the addon automatically creates Home Assistant entities:
- **Sensors**: Printer status, temperature, progress
- **Binary Sensors**: Printer online/offline, printing status
- **Devices**: Organized by printer with all related entities

### Notifications

Receive Home Assistant notifications for:
- Print job completion
- Printer errors and alerts
- File download completion
- System status changes

## Architecture Support

| Architecture | Status | Platform |
|--------------|--------|----------|
| `amd64` | ✅ Supported | Intel/AMD 64-bit |
| `armv7` | ✅ Supported | Raspberry Pi 32-bit |
| `aarch64` | ✅ Supported | Raspberry Pi 64-bit |

### Raspberry Pi Requirements

- **Model**: Raspberry Pi 4 or newer recommended
- **RAM**: 4GB minimum for optimal performance
- **Storage**: 8GB+ available space
- **Network**: Ethernet connection recommended

## Troubleshooting

### Common Issues

**Addon Won't Start**
```bash
# Check logs in Home Assistant
Settings → Add-ons → Printernizer → Logs

# Common solutions:
- Verify configuration syntax
- Check available disk space
- Ensure network connectivity to printers
```

**Printer Connection Failed**
```bash
# Bambu Lab A1:
- Verify access code from printer display
- Check IP address and network connectivity
- Ensure printer firmware is up to date

# Prusa Core One:
- Verify PrusaLink is enabled
- Check API key configuration
- Test HTTP connectivity: curl http://PRINTER_IP/api/version
```

**MQTT Discovery Not Working**
```bash
# Requirements:
- Mosquitto broker addon installed and running
- MQTT integration configured in Home Assistant
- enable_mqtt_discovery: true in addon config
```

### Performance Optimization

**Raspberry Pi Optimization**
```yaml
# Reduce polling frequency for better performance
printer_polling_interval: 60
max_concurrent_downloads: 2

# Use external database (optional)
database_path: /share/printernizer.db
```

### Logs and Debugging

**Enable Debug Logging**
```yaml
log_level: debug
```

**Access Logs**
- Home Assistant: Settings → Add-ons → Printernizer → Logs
- Container: `/data/logs/printernizer.log`
- System: `docker logs addon_printernizer`

## Development

### Local Testing

```bash
# Clone repository
git clone https://github.com/schmacka/printernizer-ha.git
cd printernizer-ha

# Build locally
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/base-python:3.11-alpine3.18" -t local/printernizer-addon .

# Test run
docker run --rm -it \
  -v $(pwd)/test-data:/data \
  -p 8000:8000 \
  local/printernizer-addon
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Test** on multiple architectures
4. **Submit** a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/schmacka/printernizer-ha/issues)
- **Discussions**: [GitHub Discussions](https://github.com/schmacka/printernizer-ha/discussions)
- **Documentation**: [Wiki](https://github.com/schmacka/printernizer-ha/wiki)
- **Upstream**: [Printernizer Project](https://github.com/schmacka/printernizer)

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

Commercial licensing available for proprietary use. Contact: sebastian@porcus3d.de

## Acknowledgments

- Built on top of [Printernizer](https://github.com/schmacka/printernizer)
- Uses [Home Assistant base images](https://github.com/home-assistant/docker-base)
- Integrates with [Home Assistant](https://www.home-assistant.io/)
- Supports [Bambu Lab](https://bambulab.com/) and [Prusa](https://www.prusa3d.com/) printers

---

**Printernizer HA Addon** - Professional 3D Printer Management for Home Assistant
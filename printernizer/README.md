# Printernizer Home Assistant Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armv7 Architecture][armv7-shield]

Professional 3D printer management system for Home Assistant. Monitor and manage your Bambu Lab A1 and Prusa Core One printers with real-time status, temperature monitoring, and MQTT discovery integration.

## About

This add-on packages the Printernizer 3D printer management system, providing comprehensive printer monitoring, job tracking, and file management capabilities optimized for Home Assistant integration.

## Features

- 🖨️ **Multi-Printer Support**: Bambu Lab A1 (MQTT) and Prusa Core One (HTTP API)
- 📊 **Real-time Monitoring**: Live printer status, job progress, and temperatures  
- 🏠 **Home Assistant Integration**: Automatic MQTT device discovery
- 📱 **Mobile Responsive**: Optimized web interface
- 🌍 **Multi-Architecture**: Supports AMD64, ARMv7, and AArch64

## Installation

1. Add this repository to your Home Assistant instance
2. Install the "Printernizer" add-on
3. Configure your printers in the add-on options
4. Start the add-on
5. Access the web interface through the "Open Web UI" button

## Configuration

### Basic Configuration

```yaml
log_level: info
web_port: 8080
mqtt_discovery: true
auto_configure_mqtt: true
printers:
  - id: "bambu_a1"
    name: "Bambu Lab A1"
    type: "bambu_lab"
    host: "192.168.1.100"
    device_id: "01234567890ABCDEF"
    serial: "01234567890ABCDEF"
    access_code: "12345678"
  - id: "prusa_core"
    name: "Prusa Core One"
    type: "prusa"
    host: "192.168.1.101"
    api_key: "your_api_key_here"
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | string | `info` | Logging level (debug, info, warning, error) |
| `web_port` | int | `8080` | Port for the web interface |
| `mqtt_discovery` | bool | `true` | Enable MQTT discovery for Home Assistant |
| `auto_configure_mqtt` | bool | `true` | Automatically configure MQTT from HA |
| `printers` | list | `[]` | List of printer configurations |

### Printer Configuration

#### Bambu Lab A1
```yaml
- id: "unique_printer_id"
  name: "Display Name"
  type: "bambu_lab"
  host: "printer_ip_address"
  device_id: "device_id_from_printer"
  serial: "serial_number"
  access_code: "access_code_from_printer"
```

#### Prusa Core One
```yaml
- id: "unique_printer_id"
  name: "Display Name"
  type: "prusa"
  host: "printer_ip_address"
  api_key: "api_key_from_printer"
```

## Home Assistant Entities

For each configured printer, the following entities are automatically created:

- **Sensors**:
  - Bed Temperature (°C)
  - Hotend Temperature (°C)
  - Print Progress (%)
  - Current File
  - Time Remaining (minutes)
  - Status (idle/printing/paused/error)

- **Binary Sensors**:
  - Printing Status (for automations)

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/schmacka/printernizer-ha).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/schmacka/printernizer-ha/blob/master/LICENSE) file for details.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
# Printernizer - Home Assistant Add-on

[![GitHub Release](https://img.shields.io/github/release/schmacka/printernizer-ha.svg)](https://github.com/schmacka/printernizer-ha/releases)
[![License](https://img.shields.io/github/license/schmacka/printernizer-ha.svg)](https://github.com/schmacka/printernizer-ha/blob/master/LICENSE)

Powerful 3D Printer Management for Home Assistant - Bambu Lab A1 and Prusa Core One support.

## ⚠️ Auto-Synced Repository

This repository is **automatically synchronized** from the main [printernizer](https://github.com/schmacka/printernizer) repository.

- **Source Code**: Automatically synced from main repo on every commit
- **HA-Specific Files**: Maintained only in this repository
- **Version Management**: Tied to main repository releases

**Do not modify `src/`, `frontend/`, or `migrations/` directly in this repository** - changes will be overwritten. Contribute to the [main repository](https://github.com/schmacka/printernizer) instead.

---

## About

Printernizer is a powerful 3D print management system designed for managing Bambu Lab A1 and Prusa Core One printers. It provides automated job tracking, file downloads, and business reporting capabilities for 3D printing operations.

### Features

- 🖨️ **Multi-Printer Support**: Manage Bambu Lab A1 and Prusa Core One printers
- 📊 **Job Tracking**: Automatic job monitoring and history
- 📁 **File Management**: Organize and manage your 3D print files
- 📈 **Analytics**: Business reporting and usage statistics
- 🎥 **Timelapses**: Automatic timelapse generation from print jobs
- 🔍 **Discovery**: Automatic printer discovery on your network
- 🌐 **Web Interface**: Beautiful, responsive web UI
- 🏠 **Home Assistant**: Native HA add-on with Ingress support

---

## Installation

### Via Home Assistant Add-on Store

1. Navigate to **Supervisor** → **Add-on Store**
2. Click the menu (⋮) and select **Repositories**
3. Add this repository: `https://github.com/schmacka/printernizer-ha`
4. Find **Printernizer** in the add-on list
5. Click **Install**
6. Configure your printers (see Configuration below)
7. Start the add-on
8. Access via the **Printernizer** panel in your sidebar

### Manual Installation

1. Copy this entire repository to `/addons/printernizer/` in your Home Assistant configuration
2. Restart Home Assistant
3. Navigate to **Supervisor** → **Add-on Store**
4. Click **Reload** to refresh the add-on list
5. Find **Printernizer (local)** and install

---

## Configuration

### Basic Configuration

The add-on can be configured through the Home Assistant UI:

```yaml
log_level: info
timezone: Europe/Berlin
discovery_timeout_seconds: 10
discovery_scan_interval_minutes: 60
timelapse_enabled: true
job_creation_auto_create: true
```

### Advanced Configuration

For detailed configuration options, see [DOCS.md](DOCS.md).

---

## Support

For issues, feature requests, or contributions:

- **Main Project**: [schmacka/printernizer](https://github.com/schmacka/printernizer)
- **This Add-on**: [schmacka/printernizer-ha](https://github.com/schmacka/printernizer-ha)

---

## License

**Free for private use.** Commercial/professional use requires a license.

See the [main repository](https://github.com/schmacka/printernizer#-license) for full licensing details.

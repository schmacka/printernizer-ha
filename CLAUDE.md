# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Auto-Synced Repository

**This repository is automatically synchronized from the main [printernizer](https://github.com/schmacka/printernizer) repository.**

### What This Means

- **Source Code**: `src/`, `frontend/`, and `migrations/` directories are **automatically synced** from the main printernizer repository
- **HA-Specific Files**: Only Home Assistant add-on configuration files are maintained here
- **Do NOT Edit**: Never modify `src/`, `frontend/`, or `migrations/` in this repository - changes will be overwritten

### To Make Code Changes

**Always edit in the main repository**: https://github.com/schmacka/printernizer

Changes will automatically sync to this repository via GitHub Actions on every push to `master` or `development` branches.

## Project Overview

**Printernizer** is a professional 3D printer fleet management system for Bambu Lab and Prusa printers, packaged as a Home Assistant add-on.

> **Tested with:** Bambu Lab A1 and Prusa Core One

**Primary Use Case**: Home Assistant integration for enterprise-grade 3D printer fleet management with automated job monitoring, file organization, and business analytics.

## Repository Structure

```
printernizer-ha/
├── repository.yaml         # HA repository metadata (EDIT HERE)
├── README.md              # Repository documentation (EDIT HERE)
└── printernizer/          # Add-on directory
    ├── config.yaml        # HA add-on configuration (EDIT HERE)
    ├── build.yaml         # Docker build configuration (EDIT HERE)
    ├── Dockerfile         # Container build instructions (EDIT HERE)
    ├── run.sh            # Add-on startup script (EDIT HERE)
    ├── requirements.txt   # Python dependencies (AUTO-SYNCED)
    ├── DOCS.md           # Add-on documentation (EDIT HERE)
    ├── CHANGELOG.md      # Version history (AUTO-SYNCED)
    ├── README.md         # Add-on README (EDIT HERE)
    ├── database_schema.sql # Database schema (AUTO-SYNCED)
    ├── icon.png          # Add-on icon (EDIT HERE)
    ├── logo.png          # Add-on logo (EDIT HERE)
    ├── src/              # Application code (AUTO-SYNCED - DO NOT EDIT)
    ├── frontend/         # Web interface (AUTO-SYNCED - DO NOT EDIT)
    └── migrations/       # Database migrations (AUTO-SYNCED - DO NOT EDIT)
```

## Files You CAN Edit

### Home Assistant Add-on Configuration

**`printernizer/config.yaml`** - Home Assistant add-on metadata and options
- Version number (updated automatically via GitHub Actions)
- Add-on name, description, slug
- Architecture support (aarch64, amd64, armv7)
- Configuration options and schema
- Ingress settings
- Port mappings
- Network requirements (host_network for printer discovery)

**`printernizer/build.yaml`** - Docker build configuration
- Base image selection
- Build arguments
- Architecture-specific builds

**`printernizer/Dockerfile`** - Container build instructions
- Base image: Home Assistant base images
- Python dependencies installation
- Application setup
- Entry point configuration

**`printernizer/run.sh`** - Add-on startup script
- Environment variable setup from HA options
- Database initialization
- Application launch

**`printernizer/DOCS.md`** - Detailed add-on documentation
- Configuration guide
- Usage instructions
- Troubleshooting

**`printernizer/README.md`** - Add-on README
- Quick overview
- Installation instructions
- Basic configuration

**`repository.yaml`** - Repository metadata
- Repository name and URL

**Repository root `README.md`** - Repository overview

## Files You CANNOT Edit (Auto-Synced)

These files are automatically synced from https://github.com/schmacka/printernizer:

- `printernizer/src/**` - Application backend code
- `printernizer/frontend/**` - Web interface
- `printernizer/migrations/**` - Database migrations
- `printernizer/requirements.txt` - Python dependencies
- `printernizer/CHANGELOG.md` - Version history
- `printernizer/database_schema.sql` - Database schema

**Any changes to these files will be overwritten on the next sync.**

## Common Development Tasks

### Updating Add-on Configuration

1. Edit `printernizer/config.yaml`
2. Update configuration options or schema
3. Test in Home Assistant
4. Commit and push changes

### Updating Documentation

1. Edit `printernizer/DOCS.md` or `printernizer/README.md`
2. Commit and push changes
3. Users will see updated docs in HA add-on store

### Updating Docker Build

1. Edit `printernizer/Dockerfile` or `printernizer/build.yaml`
2. Test build locally:
   ```bash
   cd printernizer
   docker build -t printernizer-test .
   ```
3. Commit and push changes

### Updating Startup Script

1. Edit `printernizer/run.sh`
2. Ensure environment variables are correctly mapped from HA options
3. Test in Home Assistant
4. Commit and push changes

### Version Management

**Version is managed in the main printernizer repository:**

1. Version is set in main repo's `src/main.py`
2. GitHub Actions automatically updates `printernizer/config.yaml` version on sync
3. **Do NOT manually edit version in config.yaml** - it will be overwritten

## Synchronization Process

### How Sync Works

1. Changes pushed to printernizer main repo (`master` or `development` branch)
2. GitHub Actions workflow triggers in main repo
3. Workflow copies `src/`, `frontend/`, `migrations/` to this repo
4. Version number automatically extracted and updated in `config.yaml`
5. Changes committed and pushed to this repository

### Sync Workflow

Located in main repository: `.github/workflows/sync-to-ha-repo.yml`

**Trigger events:**
- Push to `master` branch → Production sync
- Push to `development` branch → Development sync (no version bump)
- Manual workflow dispatch

## Home Assistant Add-on Specifics

### Configuration Options

Defined in `printernizer/config.yaml`:

```yaml
options:
  log_level: info
  timezone: Europe/Berlin
  discovery_timeout_seconds: 10
  discovery_scan_interval_minutes: 60
  timelapse_enabled: true
  job_creation_auto_create: true
```

### Environment Variables

Set in `run.sh` from HA options:

```bash
export LOG_LEVEL="${LOG_LEVEL:-info}"
export TIMEZONE="${TIMEZONE:-Europe/Berlin}"
export TIMELAPSE_ENABLED="${TIMELAPSE_ENABLED:-true}"
```

### Ingress Support

- Ingress enabled by default for secure access through HA UI
- Ingress port: 8000
- Optional external port exposure (disabled by default)

### Network Requirements

- **Host network mode** enabled by default
- Required for printer discovery (SSDP/mDNS multicast traffic)
- Can be disabled if discovery not needed

### Data Persistence

- `/data` directory mapped for persistence
- Database, downloads, and library stored in `/data`
- Survives add-on updates and restarts

## Testing in Home Assistant

### Local Testing

1. Copy repository to `/addons/printernizer/` in HA
2. Restart Home Assistant
3. Navigate to **Supervisor** → **Add-on Store**
4. Click **Reload**
5. Find **Printernizer (local)** and install

### Remote Testing

1. Push changes to GitHub
2. Add repository URL to Home Assistant
3. Install/update add-on
4. Check logs for issues

## Architecture Integration

### Home Assistant Features

- **Ingress**: Built-in reverse proxy for secure access
- **Supervisor API**: Integration with HA supervisor
- **Panel Integration**: Sidebar panel for easy access
- **Network Discovery**: Auto-discover printers on local network
- **Backup Support**: Hot backup of `/data` directory

### Multi-Architecture Support

Supports all HA architectures:
- `aarch64` - 64-bit ARM (Raspberry Pi 4, etc.)
- `amd64` - 64-bit x86 (Intel/AMD)
- `armv7` - 32-bit ARM (Raspberry Pi 3, etc.)

Builds use Home Assistant base images:
```yaml
build_from:
  aarch64: ghcr.io/home-assistant/aarch64-base:latest
  amd64: ghcr.io/home-assistant/amd64-base:latest
  armv7: ghcr.io/home-assistant/armv7-base:latest
```

## Troubleshooting

### Sync Issues

If files aren't syncing from main repository:
1. Check GitHub Actions in main repo: https://github.com/schmacka/printernizer/actions
2. Verify workflow `sync-to-ha-repo.yml` completed successfully
3. Check for errors in workflow logs

### Version Mismatch

If version in `config.yaml` doesn't match main repo:
1. Trigger manual sync from main repo's GitHub Actions
2. Wait for automatic sync on next push to main repo

### Build Failures

1. Check Dockerfile for syntax errors
2. Verify base image availability
3. Test build locally
4. Check Home Assistant supervisor logs

## Related Resources

- **Main Repository**: https://github.com/schmacka/printernizer
- **Aggregator Repository**: https://github.com/schmacka/homeassistant-addons
- **Issues**: https://github.com/schmacka/printernizer-ha/issues
- **Documentation**: https://schmacka.github.io/printernizer/

## Support

For issues or questions:
1. **HA Add-on specific**: Open issue in this repository
2. **Application bugs/features**: Open issue in main printernizer repository
3. **General questions**: Use GitHub Discussions in main repository

---

**Remember**: This is an auto-synced repository. Always edit application code in the main [printernizer](https://github.com/schmacka/printernizer) repository. Only edit Home Assistant-specific configuration files here.

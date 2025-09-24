# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant addon repository for **Printernizer**, which will provide 3D printer management capabilities within Home Assistant. The project will package the upstream [Printernizer](https://github.com/schmacka/printernizer) application as a Home Assistant addon.

**Current Status**: Repository is in initial setup phase with planned architecture documented below.

## Planned Architecture

This repository will follow the Home Assistant addon structure with two main components:

### Root Level (Repository Configuration)
- `config.json` - Home Assistant addon configuration defining the addon metadata, ports, architecture support, and ingress settings
- `Dockerfile` - Builds the addon by cloning the upstream Printernizer Node.js application and installing dependencies
- `repository.json` - Repository metadata for the Home Assistant addon store

### Addon Directory (`printernizer/`)
- `config.json` - Printernizer-specific configuration with 3D printer settings, print quality profiles, materials, and G-code scripts
- `Dockerfile` - Container configuration for the addon
- `README.md` - Addon documentation

## Development Commands

### Initial Setup
```bash
# Clone upstream Printernizer for reference
git clone https://github.com/schmacka/printernizer.git tmp/printernizer

# Create addon structure
mkdir -p printernizer

# Initialize repository configuration
```

### Building and Testing
Home Assistant addons are built through the Home Assistant supervisor:
```bash
# Local development requires Home Assistant OS or supervised installation
# Copy repository to /addon_configs/[repo-name]/
# Build through Home Assistant UI: Settings > Add-ons > Add-on Store
```

### Version Management
- Use semantic versioning (Major.Minor.Patch)
- Update version in both `config.json` files when making changes
- Version must be incremented for addon updates to be recognized

## Key Technologies

- **Home Assistant Addon Framework** - Uses Home Assistant's addon architecture with ingress support
- **Docker** - Multi-architecture container support (amd64, armv7, aarch64)
- **Node.js** - Upstream Printernizer application runs on Node.js
- **3D Printing Integration** - Manages FDM printers with configurable slicing profiles

## Configuration Files Structure

### Repository Configuration (`config.json`)
```json
{
  "name": "Printernizer",
  "version": "1.0.0",
  "slug": "printernizer",
  "description": "3D printer management for Home Assistant",
  "arch": ["amd64", "armv7", "aarch64"],
  "ports": {
    "8080/tcp": 8080
  },
  "ingress": true,
  "ingress_port": 8080
}
```

### Addon Configuration (`printernizer/config.json`)
Contains 3D printer profiles, materials, and G-code scripts:
- Print quality presets: draft (0.3mm), normal (0.2mm), high (0.1mm)
- Temperature settings for different materials
- Custom G-code for start/end sequences

## Development Workflow

### Setting Up Development Environment
1. Clone this repository to Home Assistant's addon directory
2. Study upstream Printernizer implementation at https://github.com/schmacka/printernizer
3. Create the addon structure following Home Assistant addon standards
4. Configure Docker build process to package the Node.js application

### Testing the Addon
1. Build through Home Assistant UI (Settings > Add-ons > Add-on Store)
2. Install and start the addon
3. Access via Home Assistant sidebar or directly at `http://[HOST]:8080/`
4. Test 3D printer connectivity and slicing functionality

## Implementation Guidelines

### File Organization
- Keep addon files in `printernizer/` subdirectory
- Root level contains repository metadata and main addon configuration
- Follow Home Assistant addon naming conventions (lowercase, hyphen-separated)

### Docker Integration
- Multi-architecture support required (amd64, armv7, aarch64)
- Clone upstream Printernizer during build process
- Install Node.js dependencies and configure port mapping
- Use Home Assistant base images when possible

### Configuration Management
- Version synchronization between root and addon config files
- Printer profiles should be configurable through Home Assistant UI
- Support common 3D printer types and materials
- Include reasonable defaults for layer heights and temperatures

### Important Notes
- Addon uses ingress routing through Home Assistant on port 8080
- Must increment version number for addon updates to be recognized
- Test on multiple architectures before release
- Follow Home Assistant addon security best practices
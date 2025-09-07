# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant addon repository for **Printernizer**, which provides 3D printer management capabilities within Home Assistant. The project packages the upstream [Printernizer](https://github.com/schmacka/printernizer) application as a Home Assistant addon.

## Architecture

This repository follows the Home Assistant addon structure with two main components:

### Root Level (Repository Configuration)
- `config.json` - Home Assistant addon configuration defining the addon metadata, ports, architecture support, and ingress settings
- `Dockerfile` - Builds the addon by cloning the upstream Printernizer Node.js application and installing dependencies
- `repository.json` - Repository metadata for the Home Assistant addon store

### Addon Directory (`printernizer/`)
- `config.json` - Printernizer-specific configuration with 3D printer settings, print quality profiles, materials, and G-code scripts
- `Dockerfile` - Python-based container (appears to be template/placeholder)
- `README.md` - Placeholder addon documentation

## Key Technologies

- **Home Assistant Addon Framework** - Uses Home Assistant's addon architecture with ingress support
- **Docker** - Multi-architecture container support (amd64, armv7, aarch64)
- **Node.js** - Upstream Printernizer application runs on Node.js
- **3D Printing Integration** - Manages FDM printers with configurable slicing profiles

## Development Workflow

### Building the Addon
The addon is built through Home Assistant's addon system:
1. Copy the repository to Home Assistant's `addons` directory
2. Build and install through the Home Assistant UI
3. Access via the sidebar at `http://[HOST]:8080/`

### Configuration Management
- Main addon config: `config.json` (ports, architecture, ingress)
- Printer settings: `printernizer/config.json` (printer profiles, materials, scripts)
- Print quality presets: draft (0.3mm), normal (0.2mm), high (0.1mm)

## Important Notes

- The addon uses ingress routing through Home Assistant on port 8080
- Supports multiple architectures for broad compatibility
- Printer configuration includes temperature settings, layer heights, and G-code scripts
- The upstream Printernizer project is cloned during Docker build process
#!/usr/bin/with-contenv bashio
# ==============================================================================
# Printernizer Home Assistant Addon
# Initialization script for container setup
# ==============================================================================
set -e

bashio::log.info "Initializing Printernizer addon..."

# Create necessary directories with proper permissions
mkdir -p /data/downloads
mkdir -p /data/logs  
mkdir -p /data/backups
mkdir -p /data/temp

# Set ownership for data directories
chown -R printernizer:printernizer /data
chmod -R 755 /data

# Initialize database if it doesn't exist
DATABASE_PATH=$(bashio::config 'database_path' '/data/printernizer.db')

if [ ! -f "${DATABASE_PATH}" ]; then
    bashio::log.info "Initializing new database at ${DATABASE_PATH}..."
    
    # Create database directory if needed
    mkdir -p "$(dirname "${DATABASE_PATH}")"
    
    # Initialize database using Printernizer's initialization
    cd /opt/printernizer/src
    python3 -c "
import asyncio
import sys
import os
sys.path.insert(0, '/opt/printernizer/src')

from database.database import Database

async def init_database():
    try:
        db = Database('${DATABASE_PATH}')
        await db.initialize()
        print('Database initialized successfully')
    except Exception as e:
        print(f'Error initializing database: {e}')
        sys.exit(1)

asyncio.run(init_database())
"
    
    # Set proper ownership
    chown printernizer:printernizer "${DATABASE_PATH}"
    chmod 664 "${DATABASE_PATH}"
    
    bashio::log.info "Database initialization complete"
else
    bashio::log.info "Existing database found at ${DATABASE_PATH}"
fi

# Validate printer configurations from addon options
if bashio::config.has_value 'printers'; then
    bashio::log.info "Validating printer configurations..."
    
    # Count configured printers
    PRINTER_COUNT=0
    for printer in $(bashio::config 'printers'); do
        PRINTER_COUNT=$((PRINTER_COUNT + 1))
    done
    
    bashio::log.info "Found ${PRINTER_COUNT} printer(s) configured"
    
    # Validate each printer configuration
    for printer in $(bashio::config 'printers'); do
        name=$(bashio::jq "${printer}" '.name')
        type=$(bashio::jq "${printer}" '.type')
        ip_address=$(bashio::jq "${printer}" '.ip_address')
        enabled=$(bashio::jq "${printer}" '.enabled // true')
        
        if [[ "${enabled}" == "true" ]]; then
            bashio::log.info "  - ${name} (${type}) at ${ip_address}"
            
            # Basic IP validation
            if ! [[ "${ip_address}" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                bashio::log.warning "    Invalid IP address format: ${ip_address}"
            fi
        else
            bashio::log.info "  - ${name} (${type}) - DISABLED"
        fi
    done
else
    bashio::log.info "No printers configured - you can add them through the web interface"
fi

# Check MQTT service availability
if bashio::config.true 'enable_mqtt_discovery'; then
    if bashio::services.available "mqtt"; then
        bashio::log.info "MQTT service available for device discovery"
    else
        bashio::log.warning "MQTT discovery enabled but MQTT service not available"
        bashio::log.warning "Please install and configure Mosquitto broker addon"
    fi
fi

# Set up log rotation
cat > /etc/logrotate.d/printernizer << EOF
/data/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    su printernizer printernizer
}
EOF

# Create application-specific directories
mkdir -p /opt/printernizer/data
ln -sf /data /opt/printernizer/data/addon-data

# Ensure proper ownership of application files
chown -R printernizer:printernizer /opt/printernizer

# Display system information for debugging
bashio::log.info "System information:"
bashio::log.info "  Architecture: $(uname -m)"
bashio::log.info "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
bashio::log.info "  Python: $(python3 --version)"
bashio::log.info "  Memory: $(free -h | grep Mem | awk '{print $2}')"
bashio::log.info "  Disk: $(df -h /data | tail -1 | awk '{print $4}') available"

bashio::log.info "Printernizer addon initialization complete"
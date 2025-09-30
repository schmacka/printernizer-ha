#!/usr/bin/env python3
"""
Home Assistant Printernizer Addon - Main Application
Simplified version of Printernizer for HA addon packaging
"""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import bashio for Home Assistant integration
try:
    import bashio
    HAS_BASHIO = True
except ImportError:
    HAS_BASHIO = False
    # Mock bashio for development
    class MockBashio:
        @staticmethod
        def config(key: str, default: Any = None) -> Any:
            env_key = f"BASHIO_{key.upper()}"
            value = os.environ.get(env_key)
            
            if value is None:
                return default
            
            # Convert string boolean values
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    return False
                # Try to convert to int
                try:
                    return int(value)
                except ValueError:
                    pass
            
            return value
        
        @staticmethod
        def info(msg: str) -> None:
            logging.info(f"[ADDON] {msg}")
        
        @staticmethod
        def warning(msg: str) -> None:
            logging.warning(f"[ADDON] {msg}")
        
        @staticmethod
        def error(msg: str) -> None:
            logging.error(f"[ADDON] {msg}")
    
    bashio = MockBashio()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
CONFIG: Dict[str, Any] = {}
PRINTERS: Dict[str, Any] = {}

def load_addon_config():
    """Load configuration from Home Assistant addon options"""
    global CONFIG, PRINTERS
    
    try:
        # Load basic configuration
        web_port = bashio.config('web_port', 8080)
        mqtt_discovery = bashio.config('mqtt_discovery', True)
        auto_configure_mqtt = bashio.config('auto_configure_mqtt', True)
        
        CONFIG = {
            'web_port': web_port,
            'log_level': bashio.config('log_level', 'info'),
            'mqtt_discovery': mqtt_discovery,
            'auto_configure_mqtt': auto_configure_mqtt,
            'database_path': '/data/printernizer.db',
            'static_files_path': '/app/static',
            'templates_path': '/app/templates'
        }
        
        # Load printer configurations
        printers_config = bashio.config('printers', [])
        PRINTERS = {}
        
        # Handle JSON string from environment variable
        if isinstance(printers_config, str):
            try:
                printers_config = json.loads(printers_config)
            except json.JSONDecodeError:
                printers_config = []
        
        for printer_config in printers_config:
            printer_id = printer_config.get('id')
            if printer_id:
                PRINTERS[printer_id] = printer_config
        
        # Load MQTT configuration if auto-configure is enabled
        if CONFIG['auto_configure_mqtt']:
            mqtt_config = {
                'host': os.environ.get('MQTT_HOST', 'core-mosquitto'),
                'port': int(os.environ.get('MQTT_PORT', '1883')),
                'username': os.environ.get('MQTT_USERNAME', ''),
                'password': os.environ.get('MQTT_PASSWORD', ''),
                'discovery_prefix': 'homeassistant'
            }
            CONFIG['mqtt'] = mqtt_config
        
        bashio.info(f"Loaded configuration for {len(PRINTERS)} printers")
        bashio.info(f"MQTT discovery: {'enabled' if CONFIG['mqtt_discovery'] else 'disabled'}")
        
    except Exception as e:
        bashio.error(f"Failed to load addon configuration: {e}")
        sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    # Startup
    bashio.info("Starting Printernizer addon...")
    load_addon_config()
    
    # Initialize database and printers here
    await initialize_printers()
    
    if CONFIG.get('mqtt_discovery'):
        await setup_mqtt_discovery()
    
    bashio.info("Printernizer addon started successfully")
    
    yield
    
    # Shutdown
    bashio.info("Shutting down Printernizer addon...")
    await cleanup_printers()

# Create FastAPI app
app = FastAPI(
    title="Printernizer HA Addon",
    description="3D Printer Management for Home Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates (will be created later)
static_path = Path(CONFIG.get('static_files_path', '/app/static'))
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates_path = Path(CONFIG.get('templates_path', '/app/templates'))
if templates_path.exists():
    templates = Jinja2Templates(directory=str(templates_path))

async def initialize_printers():
    """Initialize configured printers"""
    from printers import printer_manager
    
    for printer_id, printer_config in PRINTERS.items():
        try:
            await printer_manager.add_printer(printer_id, printer_config)
                
        except Exception as e:
            bashio.error(f"Failed to initialize printer {printer_id}: {e}")

async def setup_mqtt_discovery():
    """Setup MQTT discovery for Home Assistant"""
    if not CONFIG.get('mqtt_discovery'):
        return
    
    bashio.info("Setting up MQTT discovery...")
    
    try:
        from mqtt_discovery import setup_mqtt_discovery, MQTTConfig
        
        mqtt_config = MQTTConfig(
            host=CONFIG['mqtt']['host'],
            port=CONFIG['mqtt']['port'],
            username=CONFIG['mqtt']['username'],
            password=CONFIG['mqtt']['password'],
            discovery_prefix=CONFIG['mqtt']['discovery_prefix']
        )
        
        await setup_mqtt_discovery(mqtt_config)
        bashio.info("MQTT discovery setup completed")
        
    except Exception as e:
        bashio.error(f"Failed to setup MQTT discovery: {e}")

async def cleanup_printers():
    """Cleanup printer connections"""
    bashio.info("Cleaning up printer connections...")
    
    try:
        from printers import printer_manager
        from mqtt_discovery import stop_mqtt_discovery
        
        await printer_manager.stop_all()
        await stop_mqtt_discovery()
        
    except Exception as e:
        bashio.error(f"Error during cleanup: {e}")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main dashboard"""
    if templates_path.exists():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "printers": PRINTERS,
            "config": CONFIG
        })
    else:
        return HTMLResponse("""
        <html>
            <head><title>Printernizer HA Addon</title></head>
            <body>
                <h1>Printernizer HA Addon</h1>
                <p>3D Printer Management System</p>
                <p>Configured Printers: """ + str(len(PRINTERS)) + """</p>
                <p>MQTT Discovery: """ + ("Enabled" if CONFIG.get('mqtt_discovery') else "Disabled") + """</p>
            </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "printers": len(PRINTERS)}

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "printers": len(PRINTERS),
        "mqtt_discovery": CONFIG.get('mqtt_discovery', False),
        "version": "1.0.0"
    }

@app.get("/api/printers")
async def list_printers():
    """List all configured printers"""
    return {"printers": list(PRINTERS.keys())}

@app.get("/api/printers/{printer_id}")
async def get_printer(printer_id: str):
    """Get printer details"""
    if printer_id not in PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return {"printer": PRINTERS[printer_id]}

@app.get("/api/printers/{printer_id}/status")
async def get_printer_status(printer_id: str):
    """Get printer status"""
    if printer_id not in PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    try:
        from printers import printer_manager
        
        status = await printer_manager.get_printer_status(printer_id)
        if status:
            return status.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Printer not found in manager")
    
    except Exception as e:
        bashio.error(f"Error getting printer status: {e}")
        return {
            "printer_id": printer_id,
            "status": "error",
            "error": str(e)
        }

@app.get("/api/printers/status")
async def get_all_printer_status():
    """Get status of all printers"""
    try:
        from printers import printer_manager
        
        statuses = await printer_manager.get_all_statuses()
        return {
            "printers": {
                printer_id: status.to_dict() 
                for printer_id, status in statuses.items()
            }
        }
    
    except Exception as e:
        bashio.error(f"Error getting all printer statuses: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Load configuration
    load_addon_config()
    
    # Configure logging level
    log_level = CONFIG.get('log_level', 'info').upper()
    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))
    
    # Start the server
    port = CONFIG.get('web_port', 8080)
    bashio.info(f"Starting Printernizer on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level.lower(),
        reload=False
    )
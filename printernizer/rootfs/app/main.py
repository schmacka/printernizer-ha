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
import aiohttp
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

class SupervisorAPI:
    """Home Assistant Supervisor API integration"""
    
    def __init__(self):
        self.supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        self.base_url = "http://supervisor"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session with proper headers"""
        if not self.session:
            headers = {}
            if self.supervisor_token:
                headers['Authorization'] = f'Bearer {self.supervisor_token}'
            headers['Content-Type'] = 'application/json'
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_addon_info(self) -> Dict[str, Any]:
        """Get addon information from Supervisor"""
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/addons/self/info") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"Failed to get addon info: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting addon info: {e}")
            return {}
    
    async def get_supervisor_info(self) -> Dict[str, Any]:
        """Get Supervisor information"""
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/supervisor/info") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"Failed to get supervisor info: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting supervisor info: {e}")
            return {}
    
    async def get_homeassistant_info(self) -> Dict[str, Any]:
        """Get Home Assistant core information"""
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/core/info") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.warning(f"Failed to get HA info: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting HA info: {e}")
            return {}
    
    async def send_notification(self, message: str, title: str = "Printernizer") -> bool:
        """Send notification to Home Assistant"""
        try:
            session = await self.get_session()
            payload = {
                "message": message,
                "title": title
            }
            async with session.post(f"{self.base_url}/core/api/services/persistent_notification/create", json=payload) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

# Global Supervisor API instance
supervisor_api = SupervisorAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
CONFIG: Dict[str, Any] = {}
PRINTERS: Dict[str, Any] = {}

async def load_addon_config():
    """Load configuration from Home Assistant addon options"""
    global CONFIG, PRINTERS
    
    try:
        # Get addon and supervisor information
        addon_info = await supervisor_api.get_addon_info()
        supervisor_info = await supervisor_api.get_supervisor_info()
        ha_info = await supervisor_api.get_homeassistant_info()
        
        # Load basic configuration
        CONFIG = {
            'web_port': int(os.environ.get('API_PORT', '8000')),
            'log_level': bashio.config('log_level', 'info'),
            'database_path': bashio.config('database_path', '/data/printernizer.db'),
            'downloads_path': bashio.config('downloads_path', '/data/downloads'),
            'timezone': bashio.config('timezone', 'UTC'),
            'currency': bashio.config('currency', 'USD'),
            'vat_rate': bashio.config('vat_rate', 0.0),
            'enable_mqtt_discovery': bashio.config('enable_mqtt_discovery', True),
            'mqtt_prefix': bashio.config('mqtt_prefix', 'homeassistant'),
            'printer_polling_interval': bashio.config('printer_polling_interval', 30),
            'max_concurrent_downloads': bashio.config('max_concurrent_downloads', 5),
            'enable_notifications': bashio.config('enable_notifications', True),
            'cors_origins': bashio.config('cors_origins', ''),
            'static_files_path': '/app/static',
            'templates_path': '/app/templates',
            'ingress_url': addon_info.get('ingress_url', ''),
            'addon_slug': addon_info.get('slug', 'printernizer'),
            'addon_version': addon_info.get('version', '1.0.0'),
            'ha_version': ha_info.get('version', 'unknown'),
            'supervisor_version': supervisor_info.get('version', 'unknown')
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
        
        # Auto-configure MQTT for Home Assistant integration
        if CONFIG['enable_mqtt_discovery']:
            # Get MQTT service configuration from Supervisor
            mqtt_config = {
                'host': os.environ.get('MQTT_HOST', 'core-mosquitto'),
                'port': int(os.environ.get('MQTT_PORT', '1883')),
                'username': os.environ.get('MQTT_USERNAME', ''),
                'password': os.environ.get('MQTT_PASSWORD', ''),
                'discovery_prefix': CONFIG['mqtt_prefix']
            }
            CONFIG['mqtt'] = mqtt_config
        
        bashio.info(f"Loaded configuration for {len(PRINTERS)} printers")
        bashio.info(f"MQTT discovery: {'enabled' if CONFIG['enable_mqtt_discovery'] else 'disabled'}")
        bashio.info(f"Home Assistant version: {CONFIG['ha_version']}")
        bashio.info(f"Addon version: {CONFIG['addon_version']}")
        
        # Set up logging level
        log_level = CONFIG['log_level'].upper()
        if hasattr(logging, log_level):
            logging.getLogger().setLevel(getattr(logging, log_level))
        
    except Exception as e:
        bashio.error(f"Failed to load addon configuration: {e}")
        sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    # Startup
    bashio.info("Starting Printernizer addon...")
    await load_addon_config()
    
    # Setup static files and templates
    setup_static_files()
    
    # Initialize data management
    from backup import initialize_data_management
    await initialize_data_management(CONFIG.get('database_path', '/data').replace('printernizer.db', '').rstrip('/'))
    
    # Initialize database and printers here
    await initialize_printers()
    
    if CONFIG.get('enable_mqtt_discovery'):
        await setup_mqtt_discovery()
    
    bashio.info("Printernizer addon started successfully")
    
    # Send startup notification to Home Assistant
    if CONFIG.get('enable_notifications'):
        await supervisor_api.send_notification(
            f"Printernizer addon v{CONFIG['addon_version']} started successfully with {len(PRINTERS)} printers configured.",
            "Printernizer Started"
        )
    
    yield
    
    # Shutdown
    bashio.info("Shutting down Printernizer addon...")
    await supervisor_api.close()
    bashio.info("Shutting down Printernizer addon...")
    await cleanup_printers()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Create FastAPI app with ingress support
    app = FastAPI(
        title="Printernizer HA Addon",
        description="3D Printer Management for Home Assistant",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if os.environ.get('ENVIRONMENT') == 'development' else None,
        redoc_url="/api/redoc" if os.environ.get('ENVIRONMENT') == 'development' else None
    )
    
    # Configure CORS
    cors_origins = []
    if CONFIG.get('cors_origins'):
        cors_origins = [origin.strip() for origin in CONFIG['cors_origins'].split(',')]
    else:
        # Default CORS for Home Assistant ingress
        cors_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Add ingress support middleware
    @app.middleware("http")
    async def ingress_handler(request: Request, call_next):
        """Handle Home Assistant ingress proxy headers"""
        # Support X-Ingress-Path header for proper ingress routing
        ingress_path = request.headers.get("X-Ingress-Path", "")
        if ingress_path:
            # Update request path info for proper routing
            request.scope["path"] = request.scope["path"].replace(ingress_path, "", 1)
            if not request.scope["path"].startswith("/"):
                request.scope["path"] = "/" + request.scope["path"]
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
    
    return app

# Create the app instance (will be configured during startup)
app = create_app()

def setup_static_files():
    """Setup static files and templates after configuration is loaded"""
    # Static files
    static_path = Path('/app/static')
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    return static_path.exists()

def get_templates():
    """Get Jinja2 templates if available"""
    templates_path = Path('/app/templates')
    if templates_path.exists():
        return Jinja2Templates(directory=str(templates_path))
    return None

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
    templates = get_templates()
    if templates:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "printers": PRINTERS,
            "config": CONFIG
        })
    else:
        return HTMLResponse(f"""
        <html>
            <head><title>Printernizer HA Addon</title></head>
            <body>
                <h1>Printernizer HA Addon</h1>
                <p>3D Printer Management System for Home Assistant</p>
                <p>Addon Version: {CONFIG.get('addon_version', 'unknown')}</p>
                <p>Home Assistant Version: {CONFIG.get('ha_version', 'unknown')}</p>
                <p>Configured Printers: {len(PRINTERS)}</p>
                <p>MQTT Discovery: {'Enabled' if CONFIG.get('enable_mqtt_discovery') else 'Disabled'}</p>
                <p>Database Path: {CONFIG.get('database_path', '/data/printernizer.db')}</p>
                <a href="/api/v1/health">Health Check</a> | 
                <a href="/api/v1/info">System Info</a> |
                <a href="/api/v1/printers">Printers API</a>
            </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "printers": len(PRINTERS)}

@app.get("/api/v1/info")
async def get_addon_info():
    """Get addon and system information"""
    return {
        "addon": {
            "name": "Printernizer",
            "version": CONFIG.get('addon_version', '1.0.0'),
            "slug": CONFIG.get('addon_slug', 'printernizer')
        },
        "homeassistant": {
            "version": CONFIG.get('ha_version', 'unknown')
        },
        "supervisor": {
            "version": CONFIG.get('supervisor_version', 'unknown')
        },
        "printers": {
            "count": len(PRINTERS),
            "configured": list(PRINTERS.keys())
        },
        "features": {
            "mqtt_discovery": CONFIG.get('enable_mqtt_discovery', False),
            "notifications": CONFIG.get('enable_notifications', False),
            "ingress": bool(CONFIG.get('ingress_url'))
        }
    }

@app.get("/api/v1/config")
async def get_config():
    """Get current configuration (filtered for API consumption)"""
    return {
        "printers": len(PRINTERS),
        "mqtt_discovery": CONFIG.get('enable_mqtt_discovery', False),
        "polling_interval": CONFIG.get('printer_polling_interval', 30),
        "timezone": CONFIG.get('timezone', 'UTC'),
        "currency": CONFIG.get('currency', 'USD'),
        "version": CONFIG.get('addon_version', '1.0.0')
    }

@app.post("/api/v1/notify")
async def send_notification(request: Request):
    """Send notification to Home Assistant"""
    data = await request.json()
    message = data.get('message', '')
    title = data.get('title', 'Printernizer')
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    if CONFIG.get('enable_notifications'):
        success = await supervisor_api.send_notification(message, title)
        return {"success": success, "message": "Notification sent" if success else "Failed to send notification"}
    else:
        return {"success": False, "message": "Notifications are disabled"}

@app.get("/api/v1/backup/info")
async def get_backup_info():
    """Get information about available backups"""
    from backup import get_data_manager
    
    data_manager = await get_data_manager()
    if data_manager:
        return await data_manager.get_backup_info()
    else:
        raise HTTPException(status_code=500, detail="Data manager not initialized")

@app.post("/api/v1/backup/create")
async def create_backup(request: Request):
    """Create a new backup"""
    from backup import get_data_manager
    
    data = await request.json() if request.headers.get('content-type') == 'application/json' else {}
    include_logs = data.get('include_logs', False)
    
    data_manager = await get_data_manager()
    if data_manager:
        backup_file = await data_manager.create_backup(include_logs=include_logs)
        if backup_file:
            return {"success": True, "backup_file": backup_file, "message": "Backup created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create backup")
    else:
        raise HTTPException(status_code=500, detail="Data manager not initialized")

@app.post("/api/v1/backup/restore")
async def restore_backup(request: Request):
    """Restore from a backup file"""
    from backup import get_data_manager
    
    data = await request.json()
    backup_file = data.get('backup_file')
    
    if not backup_file:
        raise HTTPException(status_code=400, detail="Backup file path is required")
    
    data_manager = await get_data_manager()
    if data_manager:
        success = await data_manager.restore_backup(backup_file)
        if success:
            return {"success": True, "message": "Backup restored successfully. Please restart the addon."}
        else:
            raise HTTPException(status_code=500, detail="Failed to restore backup")
    else:
        raise HTTPException(status_code=500, detail="Data manager not initialized")

@app.get("/api/v1/printers")
async def list_printers():
    """List all configured printers"""
    return {"printers": list(PRINTERS.keys())}

@app.get("/api/v1/printers/{printer_id}")
async def get_printer(printer_id: str):
    """Get printer details"""
    if printer_id not in PRINTERS:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    return {"printer": PRINTERS[printer_id]}

@app.get("/api/v1/printers/{printer_id}/status")
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

@app.get("/api/v1/printers/status")
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

async def main():
    """Main function to run the addon"""
    # Load configuration
    await load_addon_config()
    
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

if __name__ == "__main__":
    asyncio.run(main())
"""
Printer Management Module for Printernizer HA Addon
Handles connections and communication with different printer types
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import aiohttp
import websockets
from paho.mqtt.client import Client as MQTTClient

logger = logging.getLogger(__name__)

class PrinterStatus(Enum):
    UNKNOWN = "unknown"
    OFFLINE = "offline"
    IDLE = "idle"
    PRINTING = "printing"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class PrinterState:
    """Represents the current state of a printer"""
    id: str
    name: str
    type: str
    status: PrinterStatus
    progress: Optional[float] = None
    current_file: Optional[str] = None
    bed_temp: Optional[float] = None
    hotend_temp: Optional[float] = None
    target_bed_temp: Optional[float] = None
    target_hotend_temp: Optional[float] = None
    print_time_remaining: Optional[int] = None
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        data['status'] = self.status.value
        return data

class BasePrinter:
    """Base class for all printer implementations"""
    
    def __init__(self, printer_id: str, config: Dict[str, Any]):
        self.id = printer_id
        self.config = config
        self.state = PrinterState(
            id=printer_id,
            name=config.get('name', printer_id),
            type=config.get('type', 'unknown'),
            status=PrinterStatus.UNKNOWN
        )
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the printer connection"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._connection_loop())
        logger.info(f"Started printer {self.id}")
    
    async def stop(self):
        """Stop the printer connection"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped printer {self.id}")
    
    async def _connection_loop(self):
        """Main connection loop - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def get_status(self) -> PrinterState:
        """Get current printer status"""
        return self.state
    
    async def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to printer"""
        raise NotImplementedError

class BambuLabPrinter(BasePrinter):
    """Bambu Lab printer implementation using MQTT"""
    
    def __init__(self, printer_id: str, config: Dict[str, Any]):
        super().__init__(printer_id, config)
        self.host = config.get('host')
        self.device_id = config.get('device_id')
        self.serial = config.get('serial')
        self.access_code = config.get('access_code')
        self.mqtt_client: Optional[MQTTClient] = None
    
    async def _connection_loop(self):
        """MQTT connection loop for Bambu Lab printer"""
        while self._running:
            try:
                await self._connect_mqtt()
                # Keep connection alive
                while self._running and self.mqtt_client and self.mqtt_client.is_connected():
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Bambu Lab printer {self.id} connection error: {e}")
                self.state.status = PrinterStatus.ERROR
                self.state.error_message = str(e)
                await asyncio.sleep(30)  # Retry after 30 seconds
    
    async def _connect_mqtt(self):
        """Connect to Bambu Lab printer via MQTT"""
        if not all([self.host, self.device_id, self.serial, self.access_code]):
            raise ValueError("Missing required Bambu Lab configuration")
        
        self.mqtt_client = MQTTClient()
        self.mqtt_client.username_pw_set("bblp", self.access_code)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.mqtt_client.connect, self.host, 8883, 60
            )
            self.mqtt_client.loop_start()
            logger.info(f"Connected to Bambu Lab printer {self.id}")
        except Exception as e:
            logger.error(f"Failed to connect to Bambu Lab printer {self.id}: {e}")
            raise
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"MQTT connected to Bambu Lab printer {self.id}")
            # Subscribe to status topics
            topic = f"device/{self.device_id}/report"
            client.subscribe(topic)
            
            # Request status
            self._request_status()
        else:
            logger.error(f"MQTT connection failed to Bambu Lab printer {self.id}: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            data = json.loads(msg.payload.decode())
            self._update_state_from_mqtt(data)
        except Exception as e:
            logger.error(f"Error processing MQTT message from {self.id}: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        logger.warning(f"MQTT disconnected from Bambu Lab printer {self.id}")
        self.state.status = PrinterStatus.OFFLINE
    
    def _update_state_from_mqtt(self, data: Dict[str, Any]):
        """Update printer state from MQTT data"""
        try:
            print_data = data.get('print', {})
            
            # Update status
            stage = print_data.get('gcode_state', 'UNKNOWN')
            if stage == 'RUNNING':
                self.state.status = PrinterStatus.PRINTING
            elif stage == 'PAUSE':
                self.state.status = PrinterStatus.PAUSED
            elif stage == 'IDLE':
                self.state.status = PrinterStatus.IDLE
            else:
                self.state.status = PrinterStatus.UNKNOWN
            
            # Update progress
            self.state.progress = print_data.get('mc_percent', 0) / 100.0
            
            # Update temperatures
            self.state.bed_temp = print_data.get('bed_temper', 0)
            self.state.hotend_temp = print_data.get('nozzle_temper', 0)
            self.state.target_bed_temp = print_data.get('bed_target_temper', 0)
            self.state.target_hotend_temp = print_data.get('nozzle_target_temper', 0)
            
            # Update file and time
            self.state.current_file = print_data.get('subtask_name')
            self.state.print_time_remaining = print_data.get('mc_remaining_time', 0) * 60  # Convert to seconds
            
            self.state.last_updated = datetime.now()
            self.state.error_message = None
            
        except Exception as e:
            logger.error(f"Error updating Bambu Lab printer {self.id} state: {e}")
    
    def _request_status(self):
        """Request status from printer"""
        if self.mqtt_client and self.mqtt_client.is_connected():
            topic = f"device/{self.device_id}/request"
            message = {
                "pushing": {
                    "sequence_id": "0",
                    "command": "pushall"
                }
            }
            self.mqtt_client.publish(topic, json.dumps(message))

class PrusaPrinter(BasePrinter):
    """Prusa printer implementation using HTTP API"""
    
    def __init__(self, printer_id: str, config: Dict[str, Any]):
        super().__init__(printer_id, config)
        self.host = config.get('host')
        self.api_key = config.get('api_key')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _connection_loop(self):
        """HTTP polling loop for Prusa printer"""
        self.session = aiohttp.ClientSession()
        
        while self._running:
            try:
                await self._poll_status()
                await asyncio.sleep(10)  # Poll every 10 seconds
            except Exception as e:
                logger.error(f"Prusa printer {self.id} polling error: {e}")
                self.state.status = PrinterStatus.ERROR
                self.state.error_message = str(e)
                await asyncio.sleep(30)  # Retry after 30 seconds
        
        if self.session:
            await self.session.close()
    
    async def _poll_status(self):
        """Poll Prusa printer status via HTTP API"""
        if not all([self.host, self.api_key]):
            raise ValueError("Missing required Prusa configuration")
        
        headers = {'X-Api-Key': self.api_key}
        
        try:
            # Get printer status
            async with self.session.get(
                f"http://{self.host}/api/printer",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await self._update_state_from_api(data)
                else:
                    logger.warning(f"Prusa printer {self.id} HTTP {response.status}")
                    self.state.status = PrinterStatus.OFFLINE
        
        except Exception as e:
            logger.error(f"Error polling Prusa printer {self.id}: {e}")
            raise
    
    async def _update_state_from_api(self, data: Dict[str, Any]):
        """Update printer state from API data"""
        try:
            state_data = data.get('state', {})
            
            # Update status
            text = state_data.get('text', '').lower()
            if 'printing' in text:
                self.state.status = PrinterStatus.PRINTING
            elif 'paused' in text:
                self.state.status = PrinterStatus.PAUSED
            elif 'operational' in text or 'ready' in text:
                self.state.status = PrinterStatus.IDLE
            elif 'error' in text:
                self.state.status = PrinterStatus.ERROR
            else:
                self.state.status = PrinterStatus.UNKNOWN
            
            # Update temperatures
            temperature = data.get('temperature', {})
            if 'bed' in temperature:
                bed = temperature['bed']
                self.state.bed_temp = bed.get('actual')
                self.state.target_bed_temp = bed.get('target')
            
            if 'extruder' in temperature:
                extruder = temperature['extruder']
                self.state.hotend_temp = extruder.get('actual')
                self.state.target_hotend_temp = extruder.get('target')
            
            self.state.last_updated = datetime.now()
            self.state.error_message = None
            
        except Exception as e:
            logger.error(f"Error updating Prusa printer {self.id} state: {e}")

class PrinterManager:
    """Manages all configured printers"""
    
    def __init__(self):
        self.printers: Dict[str, BasePrinter] = {}
    
    async def add_printer(self, printer_id: str, config: Dict[str, Any]):
        """Add a printer to management"""
        printer_type = config.get('type')
        
        if printer_type == 'bambu_lab':
            printer = BambuLabPrinter(printer_id, config)
        elif printer_type == 'prusa':
            printer = PrusaPrinter(printer_id, config)
        else:
            raise ValueError(f"Unsupported printer type: {printer_type}")
        
        self.printers[printer_id] = printer
        await printer.start()
        logger.info(f"Added printer {printer_id} ({printer_type})")
    
    async def remove_printer(self, printer_id: str):
        """Remove a printer from management"""
        if printer_id in self.printers:
            await self.printers[printer_id].stop()
            del self.printers[printer_id]
            logger.info(f"Removed printer {printer_id}")
    
    async def get_printer_status(self, printer_id: str) -> Optional[PrinterState]:
        """Get status of a specific printer"""
        if printer_id in self.printers:
            return await self.printers[printer_id].get_status()
        return None
    
    async def get_all_statuses(self) -> Dict[str, PrinterState]:
        """Get status of all printers"""
        statuses = {}
        for printer_id, printer in self.printers.items():
            statuses[printer_id] = await printer.get_status()
        return statuses
    
    async def stop_all(self):
        """Stop all printer connections"""
        for printer in self.printers.values():
            await printer.stop()
        self.printers.clear()
        logger.info("Stopped all printers")

# Global printer manager instance
printer_manager = PrinterManager()
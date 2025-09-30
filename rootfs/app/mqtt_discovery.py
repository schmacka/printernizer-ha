"""
MQTT Discovery Module for Home Assistant Integration
Automatically creates entities for printers in Home Assistant
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from aiomqtt import Client as AsyncMQTTClient
from .printers import PrinterState, PrinterStatus, printer_manager

logger = logging.getLogger(__name__)

@dataclass
class MQTTConfig:
    """MQTT configuration"""
    host: str
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    discovery_prefix: str = "homeassistant"

class MQTTDiscovery:
    """Handles MQTT discovery for Home Assistant"""
    
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client: Optional[AsyncMQTTClient] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._published_entities = set()
    
    async def start(self):
        """Start MQTT discovery"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._discovery_loop())
        logger.info("Started MQTT discovery")
    
    async def stop(self):
        """Stop MQTT discovery"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.disconnect()
        
        logger.info("Stopped MQTT discovery")
    
    async def _discovery_loop(self):
        """Main discovery loop"""
        while self._running:
            try:
                await self._connect_mqtt()
                
                # Publish discovery messages for all printers
                await self._publish_all_discoveries()
                
                # Publish state updates
                while self._running and self.client:
                    await self._publish_state_updates()
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
            except Exception as e:
                logger.error(f"MQTT discovery error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    async def _connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.client = AsyncMQTTClient(
                hostname=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password
            )
            await self.client.__aenter__()
            logger.info(f"Connected to MQTT broker at {self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    async def _publish_all_discoveries(self):
        """Publish discovery messages for all printers"""
        statuses = await printer_manager.get_all_statuses()
        
        for printer_id, state in statuses.items():
            await self._publish_printer_discovery(state)
    
    async def _publish_printer_discovery(self, state: PrinterState):
        """Publish discovery messages for a single printer"""
        printer_id = state.id
        printer_name = state.name
        
        # Device information
        device_info = {
            "identifiers": [f"printernizer_{printer_id}"],
            "name": printer_name,
            "manufacturer": "Printernizer",
            "model": state.type.title(),
            "sw_version": "1.0.0"
        }
        
        # Define entities to create
        entities = [
            # Status sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_status",
                "name": f"{printer_name} Status",
                "state_topic": f"printernizer/{printer_id}/status",
                "icon": "mdi:printer-3d",
                "device_class": None
            },
            # Progress sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_progress",
                "name": f"{printer_name} Progress",
                "state_topic": f"printernizer/{printer_id}/progress",
                "unit_of_measurement": "%",
                "icon": "mdi:progress-clock"
            },
            # Bed temperature sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_bed_temp",
                "name": f"{printer_name} Bed Temperature",
                "state_topic": f"printernizer/{printer_id}/bed_temp",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "icon": "mdi:thermometer"
            },
            # Hotend temperature sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_hotend_temp",
                "name": f"{printer_name} Hotend Temperature",
                "state_topic": f"printernizer/{printer_id}/hotend_temp",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "icon": "mdi:thermometer"
            },
            # Current file sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_current_file",
                "name": f"{printer_name} Current File",
                "state_topic": f"printernizer/{printer_id}/current_file",
                "icon": "mdi:file-document"
            },
            # Print time remaining sensor
            {
                "type": "sensor",
                "object_id": f"{printer_id}_time_remaining",
                "name": f"{printer_name} Time Remaining",
                "state_topic": f"printernizer/{printer_id}/time_remaining",
                "unit_of_measurement": "min",
                "icon": "mdi:timer"
            },
            # Binary sensor for printing status
            {
                "type": "binary_sensor",
                "object_id": f"{printer_id}_printing",
                "name": f"{printer_name} Printing",
                "state_topic": f"printernizer/{printer_id}/printing",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "running",
                "icon": "mdi:printer-3d"
            }
        ]
        
        # Publish discovery messages
        for entity in entities:
            await self._publish_entity_discovery(entity, device_info, printer_id)
    
    async def _publish_entity_discovery(self, entity: Dict[str, Any], device_info: Dict[str, Any], printer_id: str):
        """Publish discovery message for a single entity"""
        entity_type = entity.pop("type")
        object_id = entity["object_id"]
        
        # Build discovery topic
        topic = f"{self.config.discovery_prefix}/{entity_type}/{object_id}/config"
        
        # Build discovery payload
        payload = {
            **entity,
            "device": device_info,
            "unique_id": object_id,
            "availability_topic": f"printernizer/{printer_id}/availability",
            "payload_available": "online",
            "payload_not_available": "offline"
        }
        
        try:
            await self.client.publish(topic, json.dumps(payload), retain=True)
            self._published_entities.add(object_id)
            logger.debug(f"Published discovery for {object_id}")
        except Exception as e:
            logger.error(f"Failed to publish discovery for {object_id}: {e}")
    
    async def _publish_state_updates(self):
        """Publish state updates for all printers"""
        statuses = await printer_manager.get_all_statuses()
        
        for printer_id, state in statuses.items():
            await self._publish_printer_state(state)
    
    async def _publish_printer_state(self, state: PrinterState):
        """Publish state updates for a single printer"""
        printer_id = state.id
        
        try:
            # Availability
            await self.client.publish(
                f"printernizer/{printer_id}/availability",
                "online" if state.status != PrinterStatus.OFFLINE else "offline"
            )
            
            # Status
            await self.client.publish(
                f"printernizer/{printer_id}/status",
                state.status.value
            )
            
            # Progress
            progress = int(state.progress * 100) if state.progress is not None else 0
            await self.client.publish(
                f"printernizer/{printer_id}/progress",
                str(progress)
            )
            
            # Temperatures
            await self.client.publish(
                f"printernizer/{printer_id}/bed_temp",
                str(state.bed_temp) if state.bed_temp is not None else "unknown"
            )
            
            await self.client.publish(
                f"printernizer/{printer_id}/hotend_temp",
                str(state.hotend_temp) if state.hotend_temp is not None else "unknown"
            )
            
            # Current file
            await self.client.publish(
                f"printernizer/{printer_id}/current_file",
                state.current_file or "none"
            )
            
            # Time remaining (in minutes)
            time_remaining = int(state.print_time_remaining / 60) if state.print_time_remaining else 0
            await self.client.publish(
                f"printernizer/{printer_id}/time_remaining",
                str(time_remaining)
            )
            
            # Printing binary sensor
            is_printing = state.status in [PrinterStatus.PRINTING, PrinterStatus.PAUSED]
            await self.client.publish(
                f"printernizer/{printer_id}/printing",
                "ON" if is_printing else "OFF"
            )
            
        except Exception as e:
            logger.error(f"Failed to publish state for printer {printer_id}: {e}")
    
    async def remove_printer_discovery(self, printer_id: str):
        """Remove discovery messages for a printer"""
        # List of entity types and their object IDs
        entity_objects = [
            f"{printer_id}_status",
            f"{printer_id}_progress", 
            f"{printer_id}_bed_temp",
            f"{printer_id}_hotend_temp",
            f"{printer_id}_current_file",
            f"{printer_id}_time_remaining",
            f"{printer_id}_printing"
        ]
        
        entity_types = [
            "sensor", "sensor", "sensor", "sensor", "sensor", "sensor", "binary_sensor"
        ]
        
        try:
            for entity_type, object_id in zip(entity_types, entity_objects):
                topic = f"{self.config.discovery_prefix}/{entity_type}/{object_id}/config"
                await self.client.publish(topic, "", retain=True)  # Empty payload removes entity
                self._published_entities.discard(object_id)
            
            # Remove availability
            await self.client.publish(f"printernizer/{printer_id}/availability", "offline")
            
            logger.info(f"Removed MQTT discovery for printer {printer_id}")
            
        except Exception as e:
            logger.error(f"Failed to remove discovery for printer {printer_id}: {e}")

# Global MQTT discovery instance
mqtt_discovery: Optional[MQTTDiscovery] = None

async def setup_mqtt_discovery(config: MQTTConfig):
    """Setup MQTT discovery"""
    global mqtt_discovery
    
    if mqtt_discovery:
        await mqtt_discovery.stop()
    
    mqtt_discovery = MQTTDiscovery(config)
    await mqtt_discovery.start()

async def stop_mqtt_discovery():
    """Stop MQTT discovery"""
    global mqtt_discovery
    
    if mqtt_discovery:
        await mqtt_discovery.stop()
        mqtt_discovery = None
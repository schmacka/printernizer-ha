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
        if not self.client:
            return
        
        printer_id = state.printer_id
        device_info = self._get_device_info(state)
        
        # Main printer status sensor
        await self._publish_sensor(
            printer_id, "status", 
            name=f"{state.name} Status",
            device_class=None,
            icon="mdi:printer-3d",
            state_topic=f"printernizer/{printer_id}/status",
            device_info=device_info
        )
        
        # Print progress sensor
        await self._publish_sensor(
            printer_id, "progress",
            name=f"{state.name} Progress", 
            device_class=None,
            unit_of_measurement="%",
            icon="mdi:progress-check",
            state_topic=f"printernizer/{printer_id}/progress",
            device_info=device_info
        )
        
        # Temperature sensors
        if hasattr(state, 'bed_temperature'):
            await self._publish_sensor(
                printer_id, "bed_temp",
                name=f"{state.name} Bed Temperature",
                device_class="temperature", 
                unit_of_measurement="°C",
                state_topic=f"printernizer/{printer_id}/bed_temp",
                device_info=device_info
            )
        
        if hasattr(state, 'nozzle_temperature'):
            await self._publish_sensor(
                printer_id, "nozzle_temp",
                name=f"{state.name} Nozzle Temperature",
                device_class="temperature",
                unit_of_measurement="°C", 
                state_topic=f"printernizer/{printer_id}/nozzle_temp",
                device_info=device_info
            )
        
        # Binary sensors
        await self._publish_binary_sensor(
            printer_id, "printing",
            name=f"{state.name} Printing",
            device_class="running",
            state_topic=f"printernizer/{printer_id}/printing",
            device_info=device_info
        )
        
        await self._publish_binary_sensor(
            printer_id, "online", 
            name=f"{state.name} Online",
            device_class="connectivity",
            state_topic=f"printernizer/{printer_id}/online",
            device_info=device_info
        )
    
    def _get_device_info(self, state: PrinterState) -> Dict[str, Any]:
        """Get device information for Home Assistant"""
        return {
            "identifiers": [f"printernizer_{state.printer_id}"],
            "name": state.name,
            "manufacturer": state.brand if hasattr(state, 'brand') else "Unknown",
            "model": state.model if hasattr(state, 'model') else "3D Printer",
            "sw_version": getattr(state, 'firmware_version', 'unknown'),
            "via_device": "printernizer_addon"
        }
    
    async def _publish_sensor(self, printer_id: str, sensor_type: str, **kwargs):
        """Publish sensor discovery message"""
        if not self.client:
            return
        
        topic = f"{self.config.discovery_prefix}/sensor/printernizer_{printer_id}_{sensor_type}/config"
        
        config = {
            "unique_id": f"printernizer_{printer_id}_{sensor_type}",
            "object_id": f"printernizer_{printer_id}_{sensor_type}",
            "state_topic": kwargs.get('state_topic'),
            "name": kwargs.get('name'),
            "device": kwargs.get('device_info', {}),
            "availability_topic": f"printernizer/{printer_id}/available",
            "payload_available": "online",
            "payload_not_available": "offline"
        }
        
        # Add optional attributes
        if kwargs.get('device_class'):
            config['device_class'] = kwargs['device_class']
        if kwargs.get('unit_of_measurement'):
            config['unit_of_measurement'] = kwargs['unit_of_measurement']
        if kwargs.get('icon'):
            config['icon'] = kwargs['icon']
        
        await self.client.publish(topic, json.dumps(config), retain=True)
        
        # Mark as published
        entity_key = f"{printer_id}_{sensor_type}"
        self._published_entities.add(entity_key)
    
    async def _publish_binary_sensor(self, printer_id: str, sensor_type: str, **kwargs):
        """Publish binary sensor discovery message"""
        if not self.client:
            return
        
        topic = f"{self.config.discovery_prefix}/binary_sensor/printernizer_{printer_id}_{sensor_type}/config"
        
        config = {
            "unique_id": f"printernizer_{printer_id}_{sensor_type}",
            "object_id": f"printernizer_{printer_id}_{sensor_type}",
            "state_topic": kwargs.get('state_topic'),
            "name": kwargs.get('name'),
            "device": kwargs.get('device_info', {}),
            "availability_topic": f"printernizer/{printer_id}/available",
            "payload_available": "online",
            "payload_not_available": "offline",
            "payload_on": "ON",
            "payload_off": "OFF"
        }
        
        # Add optional attributes
        if kwargs.get('device_class'):
            config['device_class'] = kwargs['device_class']
        if kwargs.get('icon'):
            config['icon'] = kwargs['icon']
        
        await self.client.publish(topic, json.dumps(config), retain=True)
        
        # Mark as published
        entity_key = f"{printer_id}_{sensor_type}"
        self._published_entities.add(entity_key)
    
    async def _publish_state_updates(self):
        """Publish state updates for all printers"""
        if not self.client:
            return
        
        statuses = await printer_manager.get_all_statuses()
        
        for printer_id, state in statuses.items():
            await self._publish_printer_state(state)
    
    async def _publish_printer_state(self, state: PrinterState):
        """Publish current state for a printer"""
        if not self.client:
            return
        
        printer_id = state.printer_id
        
        try:
            # Publish availability
            await self.client.publish(f"printernizer/{printer_id}/available", "online")
            
            # Publish status
            status_value = state.status.value if hasattr(state.status, 'value') else str(state.status)
            await self.client.publish(f"printernizer/{printer_id}/status", status_value)
            
            # Publish progress
            progress = getattr(state, 'progress', 0)
            await self.client.publish(f"printernizer/{printer_id}/progress", str(progress))
            
            # Publish temperatures
            if hasattr(state, 'bed_temperature'):
                await self.client.publish(f"printernizer/{printer_id}/bed_temp", str(state.bed_temperature))
            
            if hasattr(state, 'nozzle_temperature'):
                await self.client.publish(f"printernizer/{printer_id}/nozzle_temp", str(state.nozzle_temperature))
            
            # Publish binary sensor states
            is_printing = state.status == PrinterStatus.PRINTING if hasattr(state, 'status') else False
            await self.client.publish(f"printernizer/{printer_id}/printing", "ON" if is_printing else "OFF")
            
            is_online = True  # If we're publishing, printer is reachable
            await self.client.publish(f"printernizer/{printer_id}/online", "ON" if is_online else "OFF")
            
        except Exception as e:
            logger.error(f"Error publishing state for printer {printer_id}: {e}")
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
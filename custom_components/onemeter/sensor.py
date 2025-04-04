"""Support for OneMeter sensors."""
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, SCAN_INTERVAL
from .api import (
    OneMeterApiClient, 
    OBIS_ENERGY, 
    OBIS_ENERGY_PHASE1,
    OBIS_VOLTAGE, 
    OBIS_TIMESTAMP, 
    OBIS_BATTERY_LEVEL
)

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions for available OBIS codes
SENSOR_TYPES: Dict[str, SensorEntityDescription] = {
    "energy": SensorEntityDescription(
        key="energy",
        name="Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_phase1": SensorEntityDescription(
        key="energy_phase1",
        name="Energy Phase 1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "voltage": SensorEntityDescription(
        key="voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    "battery_level": SensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-outline",
    ),
    "this_month": SensorEntityDescription(
        key="this_month",
        name="This Month Usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:calendar-month",
    ),
    "previous_month": SensorEntityDescription(
        key="previous_month",
        name="Previous Month Usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:calendar-month-outline",
    ),
    "last_update": SensorEntityDescription(
        key="last_update",
        name="Last Update",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OneMeter sensors."""
    api_key = config_entry.data[CONF_API_KEY]
    device_id = config_entry.data[CONF_DEVICE_ID]
    
    # Create API client
    client = OneMeterApiClient(device_id=device_id, api_key=api_key)
    
    # Define coordinator update method
    async def async_update_data() -> Dict[str, Any]:
        """Fetch data from the OneMeter API."""
        data: Dict[str, Any] = {}
        
        try:
            # Get device data for basic info and monthly usage
            device_data = await client.get_device_data()
            
            if device_data:
                # Extract energy values
                data["energy"] = client.extract_device_value(device_data, OBIS_ENERGY)
                data["energy_phase1"] = client.extract_device_value(device_data, OBIS_ENERGY_PHASE1)
                data["voltage"] = client.extract_device_value(device_data, OBIS_VOLTAGE)
                data["battery_level"] = client.extract_device_value(device_data, OBIS_BATTERY_LEVEL)
                
                # Extract timestamp
                timestamp_str = client.extract_device_value(device_data, OBIS_TIMESTAMP)
                if timestamp_str:
                    try:
                        data["last_update"] = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        _LOGGER.warning(f"Failed to parse timestamp: {timestamp_str}")
                        
                # Extract monthly usage
                data["this_month"] = client.get_this_month_usage(device_data)
                data["previous_month"] = client.get_previous_month_usage(device_data)
                
                return data
            else:
                raise UpdateFailed("Failed to fetch data from OneMeter API")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with OneMeter API: {err}")
    
    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="onemeter",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Create entities for available data
    entities = []
    for sensor_key, description in SENSOR_TYPES.items():
        if coordinator.data and sensor_key in coordinator.data:
            entities.append(OneMeterSensor(coordinator, description, config_entry.entry_id, device_id))
    
    async_add_entities(entities)


class OneMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a OneMeter sensor."""

    def __init__(self, coordinator, description, entry_id, device_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": "OneMeter Energy Monitor",
            "manufacturer": "OneMeter",
            "model": "Cloud Energy Monitor",
            "sw_version": "1.0",
        }
    
    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None
"""Support for OneMeter sensors."""
import logging
from datetime import datetime, timedelta
import math
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
    CONF_NAME,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    UPDATE_OFFSET_SECONDS,
    # Import all OBIS codes from const.py
    OBIS_TARIFF,
    OBIS_ENERGY_PLUS,
    OBIS_ENERGY_MINUS,
    OBIS_ENERGY_R1,
    OBIS_ENERGY_R4,
    OBIS_ENERGY_ABS,
    OBIS_POWER,
    OBIS_BATTERY_VOLTAGE,
    OBIS_METER_SERIAL,
    OBIS_UART_PARAMS,
    OBIS_METER_ERROR,
    OBIS_PHYSICAL_ADDRESS,
    OBIS_SUCCESSFUL_READINGS,
    OBIS_FAILED_READINGS_1,
    OBIS_FAILED_READINGS_2,
    OBIS_ENERGY_PLUS_T1,
    OBIS_ENERGY_PLUS_T2,
    OBIS_ENERGY_PLUS_T3,
    OBIS_ENERGY_PLUS_T4,
    OBIS_ENERGY_MINUS_T1,
    OBIS_ENERGY_MINUS_T2,
    OBIS_ENERGY_MINUS_T3,
    OBIS_ENERGY_MINUS_T4,
    OBIS_ENERGY_R1_T1,
    OBIS_ENERGY_R1_T2,
    OBIS_ENERGY_R1_T3,
    OBIS_ENERGY_R1_T4,
    OBIS_ENERGY_R4_T1,
    OBIS_ENERGY_R4_T2,
    OBIS_ENERGY_R4_T3,
    OBIS_ENERGY_R4_T4,
    OBIS_TIME,
    OBIS_DATE,
    OBIS_ACTIVE_DEMAND,
    OBIS_ACTIVE_MAX_DEMAND,
    OBIS_OPTICAL_PORT_SERIAL,
    OBIS_TEMPERATURE,
    OBIS_READOUT_TIMESTAMP,
    OBIS_READOUT_TIMESTAMP_CORRECTED,
    OBIS_ENERGY_CONSUMPTION_BLINK,
    OBIS_DEVICE_STATUS,
)
from .api import OneMeterApiClient

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions for available OBIS codes
SENSOR_TYPES: Dict[str, SensorEntityDescription] = {
    # Primary sensors
    "tariff": SensorEntityDescription(
        key="tariff",
        name="Tariff",
        icon="mdi:tag",
    ),
    "energy_plus": SensorEntityDescription(
        key="energy_plus",
        name="Energy A+ (total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_minus": SensorEntityDescription(
        key="energy_minus",
        name="Energy A- (total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-outline",
    ),
    "energy_r1": SensorEntityDescription(
        key="energy_r1",
        name="Energy R1 (total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4": SensorEntityDescription(
        key="energy_r4",
        name="Energy R4 (total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_abs": SensorEntityDescription(
        key="energy_abs",
        name="Energy |A| (total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:speedometer",
    ),
    "power": SensorEntityDescription(
        key="power",
        name="Instantaneous Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
    ),
    
    # Diagnostic sensors - visible but in diagnostics category
    "battery_voltage": SensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "meter_serial": SensorEntityDescription(
        key="meter_serial",
        name="Meter Serial Number",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "uart_params": SensorEntityDescription(
        key="uart_params",
        name="UART Communication Parameters",
        icon="mdi:router-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    
    # Hidden diagnostic sensors
    "meter_error": SensorEntityDescription(
        key="meter_error",
        name="Meter Error",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "physical_address": SensorEntityDescription(
        key="physical_address",
        name="Physical Address",
        icon="mdi:map-marker",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "successful_readings": SensorEntityDescription(
        key="successful_readings",
        name="Successful Readings Count",
        icon="mdi:check-circle-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "failed_readings_1": SensorEntityDescription(
        key="failed_readings_1",
        name="Failed Readings Count (1)",
        icon="mdi:alert",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    "failed_readings_2": SensorEntityDescription(
        key="failed_readings_2",
        name="Failed Readings Count (2)",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Additional sensors from documentation
    "energy_plus_t1": SensorEntityDescription(
        key="energy_plus_t1",
        name="Energy A+ (tariff I)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_plus_t2": SensorEntityDescription(
        key="energy_plus_t2",
        name="Energy A+ (tariff II)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_plus_t3": SensorEntityDescription(
        key="energy_plus_t3",
        name="Energy A+ (tariff III)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_plus_t4": SensorEntityDescription(
        key="energy_plus_t4",
        name="Energy A+ (tariff IV)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "energy_minus_t1": SensorEntityDescription(
        key="energy_minus_t1",
        name="Energy A- (tariff I)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-outline",
    ),
    "energy_minus_t2": SensorEntityDescription(
        key="energy_minus_t2",
        name="Energy A- (tariff II)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-outline",
    ),
    "energy_minus_t3": SensorEntityDescription(
        key="energy_minus_t3",
        name="Energy A- (tariff III)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-outline",
    ),
    "energy_minus_t4": SensorEntityDescription(
        key="energy_minus_t4",
        name="Energy A- (tariff IV)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-outline",
    ),
    "energy_r1_t1": SensorEntityDescription(
        key="energy_r1_t1",
        name="Reactive energy R1 (tariff I)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t2": SensorEntityDescription(
        key="energy_r1_t2",
        name="Reactive energy R1 (tariff II)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t3": SensorEntityDescription(
        key="energy_r1_t3",
        name="Reactive energy R1 (tariff III)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t4": SensorEntityDescription(
        key="energy_r1_t4",
        name="Reactive energy R1 (tariff IV)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t1": SensorEntityDescription(
        key="energy_r4_t1",
        name="Reactive energy R4 (tariff I)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t2": SensorEntityDescription(
        key="energy_r4_t2",
        name="Reactive energy R4 (tariff II)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t3": SensorEntityDescription(
        key="energy_r4_t3",
        name="Reactive energy R4 (tariff III)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t4": SensorEntityDescription(
        key="energy_r4_t4",
        name="Reactive energy R4 (tariff IV)",
        native_unit_of_measurement="kvarh",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "time": SensorEntityDescription(
        key="time",
        name="Time",
        icon="mdi:clock",
    ),
    "date": SensorEntityDescription(
        key="date",
        name="Date",
        icon="mdi:calendar",
    ),
    "active_demand": SensorEntityDescription(
        key="active_demand",
        name="Active Demand Current",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
    ),
    "active_max_demand": SensorEntityDescription(
        key="active_max_demand",
        name="Active Max Demand",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        icon="mdi:flash-outline",
    ),
    "optical_port_serial": SensorEntityDescription(
        key="optical_port_serial",
        name="Optical Port Serial Number",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "temperature": SensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "readout_timestamp": SensorEntityDescription(
        key="readout_timestamp",
        name="Readout Timestamp",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "readout_timestamp_corrected": SensorEntityDescription(
        key="readout_timestamp_corrected",
        name="Readout Timestamp Corrected",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "energy_consumption_blink": SensorEntityDescription(
        key="energy_consumption_blink",
        name="Energy Consumption (blink)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    "device_status": SensorEntityDescription(
        key="device_status",
        name="Device Status",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}

# Map sensor keys to OBIS codes
SENSOR_TO_OBIS_MAP = {
    "tariff": OBIS_TARIFF,
    "energy_plus": OBIS_ENERGY_PLUS,
    "energy_minus": OBIS_ENERGY_MINUS,
    "energy_r1": OBIS_ENERGY_R1,
    "energy_r4": OBIS_ENERGY_R4,
    "energy_abs": OBIS_ENERGY_ABS,
    "power": OBIS_POWER,
    "battery_voltage": OBIS_BATTERY_VOLTAGE,
    "meter_serial": OBIS_METER_SERIAL,
    "uart_params": OBIS_UART_PARAMS,
    "meter_error": OBIS_METER_ERROR,
    "physical_address": OBIS_PHYSICAL_ADDRESS,
    "successful_readings": OBIS_SUCCESSFUL_READINGS,
    "failed_readings_1": OBIS_FAILED_READINGS_1,
    "failed_readings_2": OBIS_FAILED_READINGS_2,
    # Additional mappings
    "energy_plus_t1": OBIS_ENERGY_PLUS_T1,
    "energy_plus_t2": OBIS_ENERGY_PLUS_T2,
    "energy_plus_t3": OBIS_ENERGY_PLUS_T3,
    "energy_plus_t4": OBIS_ENERGY_PLUS_T4,
    "energy_minus_t1": OBIS_ENERGY_MINUS_T1,
    "energy_minus_t2": OBIS_ENERGY_MINUS_T2,
    "energy_minus_t3": OBIS_ENERGY_MINUS_T3,
    "energy_minus_t4": OBIS_ENERGY_MINUS_T4,
    "energy_r1_t1": OBIS_ENERGY_R1_T1,
    "energy_r1_t2": OBIS_ENERGY_R1_T2,
    "energy_r1_t3": OBIS_ENERGY_R1_T3,
    "energy_r1_t4": OBIS_ENERGY_R1_T4,
    "energy_r4_t1": OBIS_ENERGY_R4_T1,
    "energy_r4_t2": OBIS_ENERGY_R4_T2,
    "energy_r4_t3": OBIS_ENERGY_R4_T3,
    "energy_r4_t4": OBIS_ENERGY_R4_T4,
    "time": OBIS_TIME,
    "date": OBIS_DATE,
    "active_demand": OBIS_ACTIVE_DEMAND,
    "active_max_demand": OBIS_ACTIVE_MAX_DEMAND,
    "optical_port_serial": OBIS_OPTICAL_PORT_SERIAL,
    "temperature": OBIS_TEMPERATURE,
    "readout_timestamp": OBIS_READOUT_TIMESTAMP,
    "readout_timestamp_corrected": OBIS_READOUT_TIMESTAMP_CORRECTED,
    "energy_consumption_blink": OBIS_ENERGY_CONSUMPTION_BLINK,
    "device_status": OBIS_DEVICE_STATUS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OneMeter sensors."""
    api_key = config_entry.data[CONF_API_KEY]
    device_id = config_entry.data[CONF_DEVICE_ID]
    
    # Get the refresh interval from options (default to 15 minutes)
    refresh_interval = config_entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)
    
    # Create API client
    client = OneMeterApiClient(device_id=device_id, api_key=api_key)
    
    # Create update coordinator
    coordinator = OneMeterUpdateCoordinator(
        hass,
        client=client,
        refresh_interval=refresh_interval,
        name=config_entry.data.get(CONF_NAME, device_id),
        device_id=device_id,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Create entities for available data
    entities = []
    for sensor_key, description in SENSOR_TYPES.items():
        if coordinator.data and sensor_key in coordinator.data:
            entities.append(OneMeterSensor(coordinator, description, config_entry.entry_id, device_id))
    
    async_add_entities(entities)


class OneMeterUpdateCoordinator(DataUpdateCoordinator):
    """Class to coordinate updates for OneMeter sensors."""
    
    def __init__(
        self, 
        hass: HomeAssistant,
        client: OneMeterApiClient,
        refresh_interval: int,
        name: str,
        device_id: str
    ) -> None:
        """Initialize the coordinator with custom update interval."""
        self.client = client
        self.device_id = device_id
        self._refresh_interval_minutes = refresh_interval
        
        # Calculate the next update time for synchronized updates
        update_interval = self._calculate_update_interval()
        
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_method=self._async_update_data,
            update_interval=update_interval,
        )
    
    def _calculate_update_interval(self) -> timedelta:
        """Calculate the time until the next synchronized update."""
        now = dt_util.now()
        
        # Calculate minutes until the next interval (1, 5, or 15 min)
        minutes_to_sync = self._refresh_interval_minutes - (now.minute % self._refresh_interval_minutes)
        
        # If we're already at an exact interval, use the full interval delay
        if minutes_to_sync == self._refresh_interval_minutes:
            minutes_to_sync = 0
        
        # Calculate seconds until the next interval + offset seconds
        seconds_to_sync = (minutes_to_sync * 60) - now.second + UPDATE_OFFSET_SECONDS
        
        # If we're too close to the next update time, add a full interval
        if seconds_to_sync < 5:  # If less than 5 seconds away
            seconds_to_sync += self._refresh_interval_minutes * 60
            
        _LOGGER.debug(
            "Calculated update interval: %s minutes, %s seconds to next sync",
            self._refresh_interval_minutes, seconds_to_sync
        )
        
        return timedelta(seconds=seconds_to_sync)
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via API and schedule next update at fixed intervals."""
        try:
            # Get the data
            data = await self.async_update_data()
            
            # Schedule the next update at a precisely timed interval
            next_update = self._calculate_update_interval()
            self.update_interval = next_update
            
            _LOGGER.debug("Next update scheduled in %s", next_update)
            
            return data
        except Exception as err:
            _LOGGER.error("Error updating OneMeter data: %s", err)
            raise UpdateFailed(f"Error updating OneMeter data: {err}") from err
    
    async def async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the OneMeter API."""
        data: Dict[str, Any] = {}
        
        try:
            # Get device data for all readings
            device_data = await self.client.get_device_data()
            
            # Get detailed readings with all OBIS codes
            all_obis_codes = list(set(SENSOR_TO_OBIS_MAP.values()))
            readings_data = await self.client.get_readings(1, all_obis_codes)
            
            if device_data or readings_data:
                # Extract all values from device data and readings
                for sensor_key, obis_code in SENSOR_TO_OBIS_MAP.items():
                    # Try to get the value from device data first
                    value = self.client.extract_device_value(device_data, obis_code)
                    
                    # If not found, try to get from readings data
                    if value is None and readings_data:
                        value = self.client.extract_reading_value(readings_data, obis_code)
                    
                    if value is not None:
                        data[sensor_key] = value
                
                # Also extract monthly usage data if available
                data["this_month"] = self.client.get_this_month_usage(device_data)
                data["previous_month"] = self.client.get_previous_month_usage(device_data)
                
                return data
            else:
                raise UpdateFailed("Failed to fetch data from OneMeter API")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with OneMeter API: {err}")


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
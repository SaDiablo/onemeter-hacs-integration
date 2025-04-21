"""Support for OneMeter sensors."""

from __future__ import annotations

import logging

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
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api import OneMeterApiClient
from .const import CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL, UNIT_REACTIVE_ENERGY
from .coordinator import OneMeterUpdateCoordinator
from .entity import OneMeterEntity

_LOGGER = logging.getLogger(__name__)

# Sensor descriptions for available OBIS codes
SENSOR_TYPES: dict[str, SensorEntityDescription] = {
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
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4": SensorEntityDescription(
        key="energy_r4",
        name="Energy R4 (total)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
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
    "battery_percentage": SensorEntityDescription(
        key="battery_percentage",
        name="Battery Percentage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
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
        name="Infrared Communication Parameters",
        icon="mdi:router-wireless",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "ir_power": SensorEntityDescription(
        key="ir_power",
        name="IR Transmission Power",
        icon="mdi:signal",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "baud_rate": SensorEntityDescription(
        key="baud_rate",
        name="IR Baud Rate",
        icon="mdi:speedometer",
        native_unit_of_measurement="bps",
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
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t2": SensorEntityDescription(
        key="energy_r1_t2",
        name="Reactive energy R1 (tariff II)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t3": SensorEntityDescription(
        key="energy_r1_t3",
        name="Reactive energy R1 (tariff III)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r1_t4": SensorEntityDescription(
        key="energy_r1_t4",
        name="Reactive energy R1 (tariff IV)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t1": SensorEntityDescription(
        key="energy_r4_t1",
        name="Reactive energy R4 (tariff I)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t2": SensorEntityDescription(
        key="energy_r4_t2",
        name="Reactive energy R4 (tariff II)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t3": SensorEntityDescription(
        key="energy_r4_t3",
        name="Reactive energy R4 (tariff III)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "energy_r4_t4": SensorEntityDescription(
        key="energy_r4_t4",
        name="Reactive energy R4 (tariff IV)",
        native_unit_of_measurement=UNIT_REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    "time": SensorEntityDescription(
        key="time",
        name="Time",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    "date": SensorEntityDescription(
        key="date",
        name="Last Total Readout",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
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
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    "readout_timestamp_corrected": SensorEntityDescription(
        key="readout_timestamp_corrected",
        name="Readout Timestamp Corrected",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the OneMeter sensors."""
    api_key = config_entry.data[CONF_API_KEY]
    device_id = config_entry.data[CONF_DEVICE_ID]

    # Get the refresh interval from options (default to 15 minutes)
    refresh_interval = config_entry.options.get(
        CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL
    )

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
            entities.append(
                OneMeterSensor(
                    coordinator, description, config_entry.entry_id, device_id
                )
            )

    async_add_entities(entities)


class OneMeterSensor(OneMeterEntity, SensorEntity):
    """Representation of a OneMeter sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: OneMeterUpdateCoordinator,
        description: SensorEntityDescription,
        entry_id: str,
        device_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.entity_description.key)
        return None

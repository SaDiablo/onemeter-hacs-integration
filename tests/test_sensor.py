"""Tests for the OneMeter sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.helpers.entity import EntityCategory

from custom_components.onemeter.sensor import (
    OneMeterSensor,
    SENSOR_TYPES,
    async_setup_entry,
)


def test_sensor_types():
    """Test that sensor types are correctly defined."""
    # Check that critical sensors are defined
    assert "energy_plus" in SENSOR_TYPES
    assert "power" in SENSOR_TYPES
    assert "battery_voltage" in SENSOR_TYPES
    assert "this_month" in SENSOR_TYPES
    assert "previous_month" in SENSOR_TYPES

    # Verify sensor configurations
    energy_sensor = SENSOR_TYPES["energy_plus"]
    assert energy_sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert energy_sensor.device_class == SensorDeviceClass.ENERGY
    assert energy_sensor.state_class == SensorStateClass.TOTAL_INCREASING

    power_sensor = SENSOR_TYPES["power"]
    assert power_sensor.native_unit_of_measurement == UnitOfPower.KILO_WATT
    assert power_sensor.device_class == SensorDeviceClass.POWER
    assert power_sensor.state_class == SensorStateClass.MEASUREMENT

    battery_sensor = SENSOR_TYPES["battery_voltage"]
    assert battery_sensor.native_unit_of_measurement == UnitOfElectricPotential.VOLT
    assert battery_sensor.device_class == SensorDeviceClass.VOLTAGE
    assert battery_sensor.entity_category == EntityCategory.DIAGNOSTIC


@pytest.mark.asyncio
async def test_sensor_creation(hass, mock_coordinator):
    """Test creating a sensor entity."""
    # Create a sensor
    description = SENSOR_TYPES["energy_plus"]
    sensor = OneMeterSensor(
        coordinator=mock_coordinator,
        description=description,
        entry_id="test_entry_id",
        device_id="test-device-id"
    )

    # Check basic entity properties
    assert sensor.unique_id == "test_entry_id_energy_plus"
    assert sensor.name == "Energy A+ (total)"
    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR

    # Check that value is retrieved from coordinator
    assert sensor.native_value == 12345.67
    assert sensor.available is True


@pytest.mark.asyncio
async def test_diagnostic_sensor_creation(hass, mock_coordinator):
    """Test creating a diagnostic sensor entity."""
    # Create a diagnostic sensor
    description = SENSOR_TYPES["battery_voltage"]
    sensor = OneMeterSensor(
        coordinator=mock_coordinator,
        description=description,
        entry_id="test_entry_id",
        device_id="test-device-id"
    )

    # Check that entity category is set properly
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.native_value == 3.6


@pytest.mark.asyncio
async def test_computed_sensor(hass, mock_coordinator):
    """Test sensor with computed value."""
    # Battery percentage is computed from voltage
    description = SENSOR_TYPES["battery_percentage"]
    sensor = OneMeterSensor(
        coordinator=mock_coordinator,
        description=description,
        entry_id="test_entry_id",
        device_id="test-device-id"
    )

    assert sensor.native_value == 95


@pytest.mark.asyncio
async def test_sensor_unavailable_state(hass):
    """Test sensor behavior when coordinator has no data."""
    # Create coordinator with no data
    coordinator = MagicMock()
    coordinator.data = None
    coordinator.name = "Test OneMeter"

    description = SENSOR_TYPES["energy_plus"]
    sensor = OneMeterSensor(
        coordinator=coordinator,
        description=description,
        entry_id="test_entry_id",
        device_id="test-device-id"
    )

    assert sensor.native_value is None


@pytest.mark.asyncio
async def test_async_setup_entry(hass, mock_config_entry, mock_api_client):
    """Test setting up sensors from a config entry."""
    # Mock coordinator
    with patch(
        "custom_components.onemeter.sensor.OneMeterUpdateCoordinator", autospec=True
    ) as mock_coordinator_class, patch(
        "custom_components.onemeter.sensor.OneMeterApiClient", return_value=mock_api_client
    ), patch(
        "custom_components.onemeter.sensor.async_add_entities"
    ) as mock_async_add_entities:
        # Set up mock coordinator instance
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.data = {
            "energy_plus": 12345.67,
            "power": 2.5,
            "battery_voltage": 3.6,
            "battery_percentage": 95,
            "meter_serial": "11722779",
            "tariff": "G11",
            "this_month": 123.45,
            "previous_month": 234.56,
        }

        # Call setup
        await async_setup_entry(hass, mock_config_entry, mock_async_add_entities)

        # Check that coordinator was created
        mock_coordinator_class.assert_called_once()

        # Check that entities were added
        mock_async_add_entities.assert_called_once()
        # Get the entities that were added
        entities = mock_async_add_entities.call_args[0][0]
        # Verify that entities were created for each sensor in the coordinator data
        assert len(entities) >= 8  # Should have at least the 8 sensors in our mock data

        # Verify sensor types
        entity_keys = set(entity.entity_description.key for entity in entities)
        assert "energy_plus" in entity_keys
        assert "power" in entity_keys
        assert "battery_voltage" in entity_keys

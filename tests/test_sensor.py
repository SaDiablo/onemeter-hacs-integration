"""Tests for the OneMeter sensor platform."""
from unittest.mock import patch, MagicMock
import pytest

from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfElectricPotential
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

from custom_components.onemeter.sensor import (
    OneMeterSensor,
    SENSOR_TYPES,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "energy_plus": 12345.67,
        "energy_minus": 10.5,
        "energy_r1": 234.56,
        "energy_r4": 456.78,
        "energy_abs": 13000.45,
        "power": 2.5,
        "battery_voltage": 3.7,
        "meter_serial": "LGZ12345678",
        "tariff": "G11",
        "this_month": 123.45,
        "previous_month": 456.78,
    }
    return coordinator


def test_sensor_types():
    """Test the sensor types are correctly defined."""
    # Check that all sensors have the required attributes
    for key, description in SENSOR_TYPES.items():
        assert description.key == key
        assert description.name is not None
        
        if key in ["energy_plus", "energy_minus", "energy_abs"]:
            assert description.device_class == SensorDeviceClass.ENERGY
            assert description.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
            assert description.state_class == SensorStateClass.TOTAL_INCREASING
        
        if key == "power":
            assert description.device_class == SensorDeviceClass.POWER
            assert description.native_unit_of_measurement == UnitOfPower.KILO_WATT
            assert description.state_class == SensorStateClass.MEASUREMENT


async def test_sensor_creation(hass, mock_coordinator):
    """Test sensor entity creation."""
    # Create a test sensor
    entity_description = SENSOR_TYPES["energy_plus"]
    sensor = OneMeterSensor(
        coordinator=mock_coordinator,
        description=entity_description,
        entry_id="test_entry_id",
        device_id="test_device_id"
    )
    
    # Check entity attributes
    assert sensor.unique_id == "test_entry_id_energy_plus"
    assert sensor.name == entity_description.name
    assert sensor.device_class == entity_description.device_class
    assert sensor.native_unit_of_measurement == entity_description.native_unit_of_measurement
    assert sensor.state_class == entity_description.state_class
    
    # Check device info
    device_info = sensor.device_info
    assert "identifiers" in device_info
    assert "name" in device_info
    assert "manufacturer" in device_info
    
    # Check state and availability
    assert sensor.available is True
    assert sensor.native_value == 12345.67


async def test_diagnostic_sensor_creation(hass, mock_coordinator):
    """Test diagnostic sensor entity creation."""
    # Create a diagnostic sensor
    entity_description = SENSOR_TYPES["battery_voltage"]
    sensor = OneMeterSensor(
        coordinator=mock_coordinator,
        description=entity_description,
        entry_id="test_entry_id",
        device_id="test_device_id"
    )
    
    # Check entity category
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    
    # Check state
    assert sensor.native_value == 3.7


@patch("custom_components.onemeter.sensor.OneMeterApiClient")
@patch("custom_components.onemeter.sensor.DataUpdateCoordinator")
@patch("custom_components.onemeter.sensor.async_add_entities")
async def test_async_setup_entry(mock_add_entities, mock_coordinator_class, mock_client_class, hass):
    """Test platform setup."""
    # Setup mocks
    mock_client = mock_client_class.return_value
    mock_client.get_device_data.return_value = {
        "lastReading": {
            "OBIS": {
                "1_8_0": 12345.67,  # Energy Plus
                "16_7_0": 2.5,      # Power
            }
        },
        "usage": {
            "thisMonth": 123.45,
            "previousMonth": 456.78,
        }
    }
    
    mock_coordinator = mock_coordinator_class.return_value
    mock_coordinator.data = {
        "energy_plus": 12345.67,
        "power": 2.5,
        "this_month": 123.45,
        "previous_month": 456.78,
    }
    
    # Test setup
    config_entry = MagicMock()
    config_entry.data = {
        "api_key": "test_api_key",
        "device_id": "test_device_id",
    }
    config_entry.entry_id = "test_entry_id"
    
    await async_setup_entry(hass, config_entry, mock_add_entities)
    
    # Verify coordinator was initialized
    mock_coordinator_class.assert_called_once()
    
    # Verify entities were added
    mock_add_entities.assert_called_once()
    # The actual number of entities depends on the mock coordinator data and available sensors
"""Tests for the OneMeter coordinator."""
from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from custom_components.onemeter.api import OneMeterApiClient
from custom_components.onemeter.coordinator import (
    OneMeterUpdateCoordinator,
    _validate_api_data
)
from custom_components.onemeter.const import SENSOR_TO_OBIS_MAP, UPDATE_OFFSET_SECONDS, DEFAULT_REFRESH_INTERVAL


@pytest.mark.asyncio
async def test_validate_api_data_success():
    """Test successful API data validation."""
    device_data = {"lastReading": {"OBIS": {}}}
    readings_data = {"readings": []}

    # This should not raise an exception
    _validate_api_data(device_data, readings_data)


@pytest.mark.asyncio
async def test_validate_api_data_missing_both():
    """Test API data validation when both data sources are missing."""
    with pytest.raises(UpdateFailed):
        _validate_api_data(None, None)


@pytest.mark.asyncio
async def test_validate_api_data_invalid_format():
    """Test API data validation with invalid data format."""
    # Invalid device data format
    with pytest.raises(UpdateFailed):
        _validate_api_data("not_a_dict", {})

    # Invalid readings data format
    with pytest.raises(UpdateFailed):
        _validate_api_data({}, "not_a_dict")

    # Missing one data source should not fail
    _validate_api_data({}, None)
    _validate_api_data(None, {})


@pytest.mark.asyncio
async def test_coordinator_init(hass: HomeAssistant):
    """Test coordinator initialization."""
    client = AsyncMock(spec=OneMeterApiClient)
    client.device_id = "test-device-id"

    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=client,
        refresh_interval=15,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    assert coordinator.client == client
    assert coordinator.device_id == "test-device-id"
    assert coordinator._refresh_interval_minutes == 15
    assert coordinator.name == "Test OneMeter"


@pytest.mark.asyncio
async def test_calculate_update_interval(hass: HomeAssistant):
    """Test calculating update interval."""
    client = AsyncMock(spec=OneMeterApiClient)
    client.device_id = "test-device-id"

    # Test with 5 minute interval
    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=client,
        refresh_interval=5,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    # Mock current time to control the calculation
    with patch('homeassistant.util.dt.now') as mock_now:
        # Test when we're at minute 17 (3 minutes before next 5-min mark)
        fake_now = dt_util.parse_datetime("2025-04-13 12:17:10")
        mock_now.return_value = fake_now

        interval = coordinator._calculate_update_interval()

        # Expected seconds to sync: (20-17)*60 - 10 + UPDATE_OFFSET_SECONDS
        expected_seconds = 3 * 60 - 10 + UPDATE_OFFSET_SECONDS
        assert interval == timedelta(seconds=expected_seconds)

        # Test when we're at exact interval
        fake_now = dt_util.parse_datetime("2025-04-13 12:15:00")
        mock_now.return_value = fake_now

        interval = coordinator._calculate_update_interval()

        # Expected seconds to sync: (0)*60 - 0 + UPDATE_OFFSET_SECONDS
        expected_seconds = UPDATE_OFFSET_SECONDS
        assert interval == timedelta(seconds=expected_seconds)

        # Test when we're too close to next update
        fake_now = dt_util.parse_datetime("2025-04-13 12:19:58")
        mock_now.return_value = fake_now

        interval = coordinator._calculate_update_interval()

        # Should add a full interval since it's less than 5 seconds away
        # Expected seconds to sync: 5*60 (seconds) + a small amount of seconds
        assert interval.total_seconds() > 5 * 60


@pytest.mark.asyncio
async def test_async_update_data(hass: HomeAssistant, mock_api_client):
    """Test the data update method."""
    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=mock_api_client,
        refresh_interval=15,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    # Mock the _calculate_update_interval method
    coordinator._calculate_update_interval = MagicMock(return_value=timedelta(seconds=30))

    # Perform the update
    data = await coordinator._async_update_data()

    # Verify API calls were made
    mock_api_client.get_device_data.assert_called_once()
    mock_api_client.get_readings.assert_called_once()

    # Verify some data was extracted correctly
    assert "energy_plus" in data
    assert "power" in data
    assert "battery_voltage" in data
    assert "this_month" in data
    assert "previous_month" in data
    assert "battery_percentage" in data

    # Check that update interval was calculated
    assert coordinator._calculate_update_interval.called
    assert coordinator.update_interval == timedelta(seconds=30)


@pytest.mark.asyncio
async def test_async_update_data_partial_failure(hass: HomeAssistant):
    """Test data update when one API call fails but the other succeeds."""
    # Create a client with device_data success but readings failure
    client = AsyncMock(spec=OneMeterApiClient)
    client.device_id = "test-device-id"
    client.get_device_data = AsyncMock(return_value={
        "lastReading": {
            "OBIS": {
                "1_8_0": 12345.67,  # Energy Plus
            }
        }
    })
    client.get_readings = AsyncMock(side_effect=Exception("API error"))
    client.extract_device_value = MagicMock(return_value=12345.67)
    client.extract_reading_value = MagicMock(return_value=None)
    client.get_this_month_usage = MagicMock(return_value=123.45)
    client.get_previous_month_usage = MagicMock(return_value=234.56)

    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=client,
        refresh_interval=15,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    # Mock the _calculate_update_interval method
    coordinator._calculate_update_interval = MagicMock(return_value=timedelta(seconds=30))

    # Perform the update
    data = await coordinator._async_update_data()

    # Verify the update still processed the device data
    assert "energy_plus" in data
    assert data["this_month"] == 123.45
    assert data["previous_month"] == 234.56


@pytest.mark.asyncio
async def test_async_update_data_both_fail(hass: HomeAssistant):
    """Test data update when both API calls fail."""
    # Create a client where both API calls fail
    client = AsyncMock(spec=OneMeterApiClient)
    client.device_id = "test-device-id"
    client.get_device_data = AsyncMock(side_effect=Exception("API error"))
    client.get_readings = AsyncMock(side_effect=Exception("API error"))

    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=client,
        refresh_interval=15,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    # Perform the update - expect it to fail
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update(hass: HomeAssistant, mock_onemeter_client):
    """Test coordinator update."""
    # Create coordinator
    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=mock_onemeter_client,
        refresh_interval=DEFAULT_REFRESH_INTERVAL,
        name="Test Device",
        device_id="device123456",
    )
    
    # Test initial refresh
    await coordinator.async_refresh()
    
    # Validate data
    assert coordinator.data is not None
    assert "energy_plus" in coordinator.data
    assert coordinator.data["energy_plus"] == 1234.56
    assert "battery_voltage" in coordinator.data
    assert coordinator.data["battery_voltage"] == 3.6
    assert "this_month" in coordinator.data
    assert coordinator.data["this_month"] == 350.75
    
    # Test next update calculation
    assert coordinator.update_interval is not None


@pytest.mark.asyncio
async def test_coordinator_error_handling(hass: HomeAssistant, mock_onemeter_client):
    """Test coordinator error handling."""
    # Create coordinator
    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=mock_onemeter_client,
        refresh_interval=DEFAULT_REFRESH_INTERVAL,
        name="Test Device",
        device_id="device123456",
    )
    
    # Make client.get_device_data raise an exception
    mock_onemeter_client.get_device_data.side_effect = Exception("API error")
    
    # Refresh should handle the exception
    await coordinator.async_refresh()
    
    # Check that the coordinator properly handled the exception
    assert coordinator.last_update_success is False

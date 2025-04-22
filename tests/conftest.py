"""Fixtures for OneMeter tests."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.onemeter.api import OneMeterApiClient
from custom_components.onemeter.const import CONF_API_KEY, CONF_DEVICE_ID, DOMAIN
from custom_components.onemeter.coordinator import OneMeterUpdateCoordinator


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Return a mock OneMeter API client."""
    client = AsyncMock(spec=OneMeterApiClient)
    client.device_id = "test-device-id"
    client.api_key = "test-api-key"

    # Setup API responses
    client.get_device_data = AsyncMock(return_value={
        "lastReading": {
            "OBIS": {
                "1_8_0": 12345.67,  # Energy Plus
                "2_8_0": 0.0,       # Energy Minus
                "5_8_0": 2305.99,   # Energy R1
                "8_8_0": 3061.36,   # Energy R4
                "15_8_0": 12345.67, # Energy |A|
                "16_7_0": 2.5,      # Power
                "S_1_1_2": 3.6,     # Battery voltage
                "C_1_0": "11722779",# Meter Serial
                "0_2_2": "G11"      # Tariff
            }
        },
        "usage": {
            "thisMonth": 123.45,
            "previousMonth": 234.56,
        }
    })

    client.get_readings = AsyncMock(return_value={
        "readings": [{
            "OBIS": {
                "1_8_0": 12345.67,
                "16_7_0": 2.5,
            },
            "date": "2025-04-13T12:00:00.000Z"
        }]
    })

    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Return a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_API_KEY: "test-api-key",
        CONF_DEVICE_ID: "test-device-id",
        "name": "Test OneMeter"
    }
    entry.options = {
        "refresh_interval": 15
    }
    entry.title = "Test OneMeter"
    entry.domain = DOMAIN
    entry.unique_id = "test-device-id"
    return entry


@pytest.fixture
async def mock_coordinator(hass, mock_api_client) -> OneMeterUpdateCoordinator:
    """Return a mock coordinator."""
    coordinator = OneMeterUpdateCoordinator(
        hass=hass,
        client=mock_api_client,
        refresh_interval=15,
        name="Test OneMeter",
        device_id="test-device-id"
    )

    coordinator.data = {
        "energy_plus": 12345.67,
        "energy_minus": 0.0,
        "energy_r1": 2305.99,
        "energy_r4": 3061.36,
        "energy_abs": 12345.67,
        "power": 2.5,
        "battery_voltage": 3.6,
        "battery_percentage": 95,
        "meter_serial": "11722779",
        "tariff": "G11",
        "this_month": 123.45,
        "previous_month": 234.56,
    }

    return coordinator

"""Pytest configuration for the OneMeter integration tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the custom_components directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Now we can import the components after path setup
from custom_components.onemeter.api import OneMeterApiClient

# Mock API responses
MOCK_DEVICE_ID = "device123456"
MOCK_API_KEY = "api_key_12345"


@pytest.fixture
def mock_onemeter_client():
    """Mock the OneMeter API client."""
    client = MagicMock(spec=OneMeterApiClient)
    client.device_id = MOCK_DEVICE_ID
    client.api_key = MOCK_API_KEY

    # Mock async methods
    client.get_device_data = AsyncMock(
        return_value={
            "OBIS": {
                "1_8_0": {"value": 1234.56},  # Energy plus
                "2_8_0": {"value": 0.0},      # Energy minus
                "S_1_1_2": {"value": 3.6},    # Battery voltage
            },
            "lastReading": {
                "timestamp": 1675000000
            }
        }
    )

    client.get_readings = AsyncMock(
        return_value={
            "readings": [
                {
                    "timestamp": 1675000000,
                    "OBIS": {
                        "1_8_0": {"value": 1234.56},
                        "16_7_0": {"value": 2.5}  # Power
                    }
                }
            ]
        }
    )

    client.get_this_month_usage = MagicMock(return_value=350.75)
    client.get_previous_month_usage = MagicMock(return_value=425.25)
    client.extract_device_value = MagicMock(return_value=None)
    client.extract_reading_value = MagicMock(return_value=None)

    # Set up specific mock values for key attributes
    def extract_device_value_side_effect(data, obis_code):
        if obis_code == "1_8_0":
            return 1234.56
        elif obis_code == "2_8_0":
            return 0.0
        elif obis_code == "S_1_1_2":
            return 3.6
        return None

    def extract_reading_value_side_effect(data, obis_code):
        if obis_code == "16_7_0":
            return 2.5
        return None

    client.extract_device_value.side_effect = extract_device_value_side_effect
    client.extract_reading_value.side_effect = extract_reading_value_side_effect

    client.close = AsyncMock()

    return client


@pytest.fixture
def hass_storage():
    """Fixture to mock the hass storage."""
    return {}


@pytest.fixture
def hass_config_entries():
    """Fixture to mock the config entries data."""
    return {}


@pytest.fixture
def mock_get_available_devices():
    """Mock the get_available_devices function."""
    with patch(
        "custom_components.onemeter.config_flow.get_available_devices",
        return_value=[
            {
                "_id": MOCK_DEVICE_ID,
                "info": {"name": "My OneMeter Device"}
            }
        ],
    ) as mock:
        yield mock

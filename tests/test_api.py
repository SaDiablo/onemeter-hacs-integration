"""Tests for the OneMeter API client."""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from custom_components.onemeter.api import OneMeterApiClient, OBIS_ENERGY_PLUS, OBIS_POWER


class TestOneMeterApiClient(unittest.TestCase):
    """Test the OneMeter API client."""

    def setUp(self):
        """Set up test variables."""
        self.device_id = "test-device-id"
        self.api_key = "test-api-key"
        self.client = OneMeterApiClient(device_id=self.device_id, api_key=self.api_key)

    def test_initialization(self):
        """Test initialization of OneMeter API client."""
        self.assertEqual(self.client.device_id, self.device_id)
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertIsNotNone(self.client.base_url)
        self.assertIsNotNone(self.client.headers)
        self.assertEqual(self.client.headers["Authorization"], self.api_key)

    @patch("custom_components.onemeter.api.requests.get")
    def test_get_device_data(self, mock_get):
        """Test getting device data."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "lastReading": {
                "OBIS": {
                    "1_8_0": 12345.67,  # Energy Plus
                    "16_7_0": 2.5,  # Power
                    "S_1_1_2": 3.6,  # Battery voltage
                }
            },
            "usage": {
                "thisMonth": 123.45,
                "previousMonth": 234.56,
            }
        }
        mock_get.return_value = mock_response

        # Call method
        result = self.client.get_device_data()

        # Assertions
        mock_get.assert_called_once_with(
            f"{self.client.base_url}/devices/{self.device_id}",
            headers=self.client.headers
        )
        self.assertEqual(result["lastReading"]["OBIS"]["1_8_0"], 12345.67)
        self.assertEqual(result["usage"]["thisMonth"], 123.45)

    @patch("custom_components.onemeter.api.requests.get")
    def test_get_readings(self, mock_get):
        """Test getting readings data."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "readings": [
                {
                    "1_8_0": 12345.67,
                    "date": "2023-01-01T00:00:00.000Z"
                }
            ],
            "meta": {
                "OBIS": {
                    "1_8_0": {
                        "key": "POSITIVE_ACTIVE_ENERGY_TOTAL"
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        # Call method
        result = self.client.get_readings(1, ["1_8_0"])

        # Assertions
        self.assertEqual(result["readings"][0]["1_8_0"], 12345.67)

    def test_extract_device_value(self):
        """Test extracting values from device data."""
        device_data = {
            "lastReading": {
                "OBIS": {
                    "1_8_0": 12345.67,
                    "16_7_0": 2.5,
                }
            }
        }

        # Test existing values
        self.assertEqual(self.client.extract_device_value(device_data, OBIS_ENERGY_PLUS), 12345.67)
        self.assertEqual(self.client.extract_device_value(device_data, OBIS_POWER), 2.5)

        # Test non-existent value
        self.assertIsNone(self.client.extract_device_value(device_data, "non_existent"))

    def test_extract_reading_value(self):
        """Test extracting values from readings data."""
        readings_data = {
            "readings": [
                {
                    "1_8_0": 12345.67,
                    "date": "2023-01-01T00:00:00.000Z"
                }
            ]
        }

        # Test existing values
        self.assertEqual(self.client.extract_reading_value(readings_data, OBIS_ENERGY_PLUS), 12345.67)

        # Test non-existent value
        self.assertIsNone(self.client.extract_reading_value(readings_data, "non_existent"))

    def test_get_this_month_usage(self):
        """Test getting this month's usage."""
        device_data = {
            "usage": {
                "thisMonth": 123.45
            }
        }

        self.assertEqual(self.client.get_this_month_usage(device_data), 123.45)
        self.assertIsNone(self.client.get_this_month_usage({}))

    def test_get_previous_month_usage(self):
        """Test getting previous month's usage."""
        device_data = {
            "usage": {
                "previousMonth": 234.56
            }
        }

        self.assertEqual(self.client.get_previous_month_usage(device_data), 234.56)
        self.assertIsNone(self.client.get_previous_month_usage({}))

    @patch("custom_components.onemeter.api.requests.get")
    def test_api_error_handling(self, mock_get):
        """Test API error handling."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_get.return_value = mock_response

        # Test that exception is raised
        with self.assertRaises(Exception):
            self.client.get_device_data()

        # Test connection error
        mock_get.side_effect = Exception("Connection error")
        with self.assertRaises(Exception):
            self.client.get_device_data()


async def test_api_client_get_device_data():
    """Test the get_device_data method."""
    client = OneMeterApiClient(device_id="test123", api_key="api_key_test")

    # Mock the api_call method
    client.api_call = AsyncMock(return_value={
        "OBIS": {
            "1_8_0": {"value": 1234.56},
            "S_1_1_2": {"value": 3.6}
        }
    })

    # Call the method
    result = await client.get_device_data()

    # Verify the result
    assert result is not None
    assert "OBIS" in result
    assert result["OBIS"]["1_8_0"]["value"] == 1234.56

    # Verify the api_call was called with correct parameters
    client.api_call.assert_called_once_with(f"devices/{client.device_id}")


async def test_api_client_get_readings():
    """Test the get_readings method."""
    client = OneMeterApiClient(device_id="test123", api_key="api_key_test")

    # Mock the api_call method
    client.api_call = AsyncMock(return_value={
        "readings": [
            {
                "timestamp": 1675000000,
                "OBIS": {
                    "1_8_0": {"value": 1234.56},
                    "16_7_0": {"value": 2.5}
                }
            }
        ]
    })

    # Call the method with parameters
    result = await client.get_readings(count=1, obis_codes=["1_8_0", "16_7_0"])

    # Verify the result
    assert result is not None
    assert "readings" in result
    assert len(result["readings"]) == 1
    assert result["readings"][0]["OBIS"]["1_8_0"]["value"] == 1234.56

    # Verify the api_call was called with correct parameters
    client.api_call.assert_called_once_with(
        f"devices/{client.device_id}/readings",
        {"count": 1, "codes": "1_8_0,16_7_0"}
    )


async def test_extract_device_value():
    """Test the extract_device_value method."""
    client = OneMeterApiClient(device_id="test123", api_key="api_key_test")

    # Test valid data
    data = {
        "OBIS": {
            "1_8_0": {"value": 1234.56},
            "empty_value": {},
            "null_value": {"value": None}
        }
    }

    # Test successful extraction
    assert client.extract_device_value(data, "1_8_0") == 1234.56

    # Test missing OBIS code
    assert client.extract_device_value(data, "not_exists") is None

    # Test empty value
    assert client.extract_device_value(data, "empty_value") is None

    # Test null value
    assert client.extract_device_value(data, "null_value") is None

    # Test invalid data
    assert client.extract_device_value(None, "1_8_0") is None
    assert client.extract_device_value({}, "1_8_0") is None
    assert client.extract_device_value({"OBIS": None}, "1_8_0") is None

"""Tests for the OneMeter API client."""
import unittest
from unittest.mock import patch, MagicMock

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
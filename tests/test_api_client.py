"""Tests for the OneMeter API client."""
from __future__ import annotations

import asyncio
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.onemeter.api import (
    OneMeterApiClient,
    OneMeterApiError,
    OneMeterAuthError,
    OneMeterRateLimitError,
    OBIS_ENERGY_PLUS,
    OBIS_POWER,
    RESP_DEVICES,
    RESP_LAST_READING,
    RESP_OBIS,
    RESP_USAGE,
    RESP_THIS_MONTH,
    RESP_PREV_MONTH,
)


@pytest.fixture
def onemeter_client():
    """Create a test instance of OneMeterApiClient."""
    return OneMeterApiClient(device_id="test-device-id", api_key="test-api-key")


@pytest.mark.asyncio
async def test_client_initialization(onemeter_client):
    """Test OneMeter client initialization."""
    assert onemeter_client.device_id == "test-device-id"
    assert onemeter_client.api_key == "test-api-key"
    assert onemeter_client._session is None


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
async def test_create_session(mock_client_session, onemeter_client):
    """Test creating a client session."""
    session_instance = MagicMock()
    mock_client_session.return_value = session_instance

    result = await onemeter_client._create_session()

    mock_client_session.assert_called_once()
    assert result == session_instance
    assert onemeter_client._session == session_instance

    # Test reusing existing session
    mock_client_session.reset_mock()
    onemeter_client._session.closed = False
    result = await onemeter_client._create_session()

    mock_client_session.assert_not_called()
    assert result == session_instance


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
async def test_api_call_success(mock_client_session, onemeter_client):
    """Test successful API call."""
    # Setup mock session and response
    session_mock = MagicMock()
    response_mock = AsyncMock()
    response_mock.status = HTTPStatus.OK
    response_mock.json.return_value = {"data": "test_data"}

    # Setup context managers
    session_mock.get.return_value.__aenter__.return_value = response_mock
    mock_client_session.return_value = session_mock

    result = await onemeter_client.api_call("test-endpoint")

    # Verify call was made correctly
    session_mock.get.assert_called_once()
    response_mock.json.assert_called_once()
    assert result == {"data": "test_data"}


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
@patch("custom_components.onemeter.api.asyncio.sleep")
async def test_api_call_retry(mock_sleep, mock_client_session, onemeter_client):
    """Test API call retry mechanism."""
    # Set up session and two responses: first fails, second succeeds
    session_mock = MagicMock()
    failed_response = AsyncMock()
    failed_response.status = HTTPStatus.INTERNAL_SERVER_ERROR
    failed_response.text.return_value = "Server error"

    success_response = AsyncMock()
    success_response.status = HTTPStatus.OK
    success_response.json.return_value = {"data": "retry_success"}

    # First call returns failure, second returns success
    session_mock.get.return_value.__aenter__.side_effect = [
        failed_response, success_response
    ]

    mock_client_session.return_value = session_mock

    result = await onemeter_client.api_call("test-endpoint")

    # Verify retry happened
    assert session_mock.get.call_count == 2
    mock_sleep.assert_called_once()
    assert result == {"data": "retry_success"}


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
async def test_api_call_auth_error(mock_client_session, onemeter_client):
    """Test API call with authentication error."""
    # Setup mock session and error response
    session_mock = MagicMock()
    response_mock = AsyncMock()
    response_mock.status = HTTPStatus.UNAUTHORIZED
    response_mock.text.return_value = "Unauthorized"

    session_mock.get.return_value.__aenter__.return_value = response_mock
    mock_client_session.return_value = session_mock

    result = await onemeter_client.api_call("test-endpoint")

    # Verify no retry attempted for auth errors
    session_mock.get.assert_called_once()
    assert result == {}


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
async def test_api_call_rate_limit(mock_client_session, onemeter_client):
    """Test API call with rate limit error."""
    # Setup mock session and rate limit response
    session_mock = MagicMock()
    response_mock = AsyncMock()
    response_mock.status = HTTPStatus.TOO_MANY_REQUESTS
    response_mock.text.return_value = "Rate limited"

    session_mock.get.return_value.__aenter__.return_value = response_mock
    mock_client_session.return_value = session_mock

    result = await onemeter_client.api_call("test-endpoint")

    # Verify no retry attempted for rate limit errors
    session_mock.get.assert_called_once()
    assert result == {}


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
@patch("custom_components.onemeter.api.asyncio.sleep")
async def test_api_call_timeout(mock_sleep, mock_client_session, onemeter_client):
    """Test API call with timeout error."""
    # Setup mock session to raise timeout
    session_mock = MagicMock()
    session_mock.get.return_value.__aenter__.side_effect = asyncio.TimeoutError
    mock_client_session.return_value = session_mock

    await onemeter_client.api_call("test-endpoint")

    # Verify retry was attempted
    assert session_mock.get.call_count > 1
    mock_sleep.assert_called()


@pytest.mark.asyncio
async def test_get_all_devices(onemeter_client):
    """Test getting all devices."""
    # Replace api_call method with a mock
    onemeter_client.api_call = AsyncMock(return_value={"devices": [{"id": "device1"}]})

    result = await onemeter_client.get_all_devices()

    onemeter_client.api_call.assert_called_once_with("devices")
    assert result == {"devices": [{"id": "device1"}]}


@pytest.mark.asyncio
async def test_get_device_data(onemeter_client):
    """Test getting device data."""
    # Replace api_call method with a mock
    onemeter_client.api_call = AsyncMock(return_value={"id": "test-device-id"})

    result = await onemeter_client.get_device_data()

    onemeter_client.api_call.assert_called_once_with(f"devices/{onemeter_client.device_id}")
    assert result == {"id": "test-device-id"}


@pytest.mark.asyncio
async def test_get_readings(onemeter_client):
    """Test getting readings data."""
    # Replace api_call method with a mock
    onemeter_client.api_call = AsyncMock(return_value={"readings": []})

    # Test with default parameters
    await onemeter_client.get_readings()
    onemeter_client.api_call.assert_called_once()

    # Test with custom parameters
    onemeter_client.api_call.reset_mock()
    obis_codes = ["1_8_0", "16_7_0"]
    await onemeter_client.get_readings(count=5, obis_codes=obis_codes)

    onemeter_client.api_call.assert_called_once()
    call_args = onemeter_client.api_call.call_args
    assert call_args[0][0] == f"devices/{onemeter_client.device_id}/readings"
    assert "obis" in call_args[0][1]
    assert call_args[0][1]["count"] == 5


def test_extract_device_value(onemeter_client):
    """Test extracting values from device data."""
    # Test with valid data
    device_data = {
        RESP_LAST_READING: {
            RESP_OBIS: {
                "1_8_0": 12345.67,
                "16_7_0": 2.5,
            }
        }
    }

    assert onemeter_client.extract_device_value(device_data, "1_8_0") == 12345.67
    assert onemeter_client.extract_device_value(device_data, "16_7_0") == 2.5
    assert onemeter_client.extract_device_value(device_data, "non_existent") is None

    # Test with nested device structure
    nested_data = {
        RESP_DEVICES: [{
            RESP_LAST_READING: {
                RESP_OBIS: {
                    "1_8_0": 9999.99
                }
            }
        }]
    }

    assert onemeter_client.extract_device_value(nested_data, "1_8_0") == 9999.99

    # Test with empty/invalid data
    assert onemeter_client.extract_device_value({}, "1_8_0") is None
    assert onemeter_client.extract_device_value(None, "1_8_0") is None
    assert onemeter_client.extract_device_value("invalid", "1_8_0") is None


def test_extract_reading_value(onemeter_client):
    """Test extracting values from readings data."""
    # Test with valid data
    readings_data = {
        "readings": [{
            RESP_OBIS: {
                "1_8_0": 12345.67,
                "16_7_0": 2.5,
            },
            "date": "2025-04-13T12:00:00.000Z"
        }]
    }

    assert onemeter_client.extract_reading_value(readings_data, "1_8_0") == 12345.67
    assert onemeter_client.extract_reading_value(readings_data, "16_7_0") == 2.5
    assert onemeter_client.extract_reading_value(readings_data, "non_existent") is None

    # Test with direct keys in reading
    direct_readings_data = {
        "readings": [{
            "1_8_0": 9876.54,
            "date": "2025-04-13T12:00:00.000Z"
        }]
    }

    assert onemeter_client.extract_reading_value(direct_readings_data, "1_8_0") == 9876.54

    # Test with empty/invalid data
    assert onemeter_client.extract_reading_value({}, "1_8_0") is None
    assert onemeter_client.extract_reading_value(None, "1_8_0") is None
    assert onemeter_client.extract_reading_value("invalid", "1_8_0") is None


def test_get_this_month_usage(onemeter_client):
    """Test getting this month's usage."""
    # Test with valid data
    device_data = {
        RESP_USAGE: {
            RESP_THIS_MONTH: 123.45
        }
    }

    assert onemeter_client.get_this_month_usage(device_data) == 123.45

    # Test with nested device structure
    nested_data = {
        RESP_DEVICES: [{
            RESP_USAGE: {
                RESP_THIS_MONTH: 678.90
            }
        }]
    }

    assert onemeter_client.get_this_month_usage(nested_data) == 678.90

    # Test with empty/invalid data
    assert onemeter_client.get_this_month_usage({}) is None
    assert onemeter_client.get_this_month_usage(None) is None
    assert onemeter_client.get_this_month_usage({RESP_USAGE: {}}) is None


def test_get_previous_month_usage(onemeter_client):
    """Test getting previous month's usage."""
    # Test with valid data
    device_data = {
        RESP_USAGE: {
            RESP_PREV_MONTH: 234.56
        }
    }

    assert onemeter_client.get_previous_month_usage(device_data) == 234.56

    # Test with nested device structure
    nested_data = {
        RESP_DEVICES: [{
            RESP_USAGE: {
                RESP_PREV_MONTH: 789.01
            }
        }]
    }

    assert onemeter_client.get_previous_month_usage(nested_data) == 789.01

    # Test with empty/invalid data
    assert onemeter_client.get_previous_month_usage({}) is None
    assert onemeter_client.get_previous_month_usage(None) is None
    assert onemeter_client.get_previous_month_usage({RESP_USAGE: {}}) is None


@pytest.mark.asyncio
@patch("custom_components.onemeter.api.aiohttp.ClientSession")
async def test_close_session(mock_client_session, onemeter_client):
    """Test closing the API client session."""
    # Create a mock session
    mock_session = AsyncMock()
    mock_client_session.return_value = mock_session

    # Create a session then close it
    await onemeter_client._create_session()
    await onemeter_client.close()

    # Verify session was closed
    mock_session.close.assert_called_once()
    assert onemeter_client._session is None

    # Test closing when no session exists
    mock_session.reset_mock()
    await onemeter_client.close()
    mock_session.close.assert_not_called()

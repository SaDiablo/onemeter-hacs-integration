"""API client for OneMeter Cloud API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Final, TypedDict, NotRequired, cast

import aiohttp
from aiohttp import ClientSession

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    API_RETRY_ATTEMPTS,
    API_RETRY_DELAY,
    OBIS_BATTERY_VOLTAGE,
    OBIS_ENERGY_ABS,
    OBIS_ENERGY_MINUS,
    OBIS_ENERGY_PLUS,
    OBIS_ENERGY_R1,
    OBIS_ENERGY_R4,
    OBIS_METER_SERIAL,
    OBIS_POWER,
    OBIS_TARIFF,
    RESP_DEVICES,
    RESP_LAST_READING,
    RESP_OBIS,
    RESP_PREV_MONTH,
    RESP_THIS_MONTH,
    RESP_USAGE,
)

_LOGGER = logging.getLogger(__name__)


class OneMeterApiError(Exception):
    """Exception raised for OneMeter API errors."""

    def __init__(self, status_code: int | None = None, message: str = ""):
        """Initialize the exception."""
        self.status_code = status_code
        self.message = message
        super().__init__(f"OneMeter API error: {status_code} - {message}")


class OneMeterAuthError(OneMeterApiError):
    """Exception raised for authentication errors."""


class OneMeterRateLimitError(OneMeterApiError):
    """Exception raised when rate limited by the API."""


class OneMeterApiResponseDict(TypedDict):
    """Type definition for API response data."""

    error: NotRequired[str]


class OneMeterApiClient:
    """API client for OneMeter Cloud."""

    def __init__(self, device_id: str, api_key: str) -> None:
        """Initialize the client."""
        self.device_id: Final = device_id
        self.api_key: Final = api_key
        self._session: ClientSession | None = None

    async def _create_session(self) -> ClientSession:
        """Create session if needed and return it."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def api_call(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an API call with retry logic."""
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"Authorization": self.api_key}

        session = await self._create_session()

        for attempt in range(API_RETRY_ATTEMPTS):
            try:
                async with asyncio.timeout(API_TIMEOUT):
                    async with session.get(
                        url, headers=headers, params=params
                    ) as response:
                        if response.status == 200:
                            return cast(dict[str, Any], await response.json())

                        response_text = await response.text()

                        # Handle specific error codes
                        if response.status == 401:
                            raise OneMeterAuthError(response.status, "Invalid API key or unauthorized access")
                        elif response.status == 429:
                            raise OneMeterRateLimitError(response.status, "Rate limit exceeded")
                        elif response.status >= 500:
                            # Server errors may be temporary, will retry
                            _LOGGER.warning(
                                "OneMeter API server error (attempt %s/%s): %s - %s",
                                attempt + 1,
                                API_RETRY_ATTEMPTS,
                                response.status,
                                response_text,
                            )
                        else:
                            # Client errors (4xx) are likely not recoverable after the first attempt
                            _LOGGER.error(
                                "OneMeter API client error: %s - %s",
                                response.status,
                                response_text,
                            )
                            return {}

            except (TimeoutError, asyncio.TimeoutError):
                _LOGGER.warning(
                    "API timeout (attempt %s/%s) for %s",
                    attempt + 1,
                    API_RETRY_ATTEMPTS,
                    url,
                )
            except (OneMeterAuthError, OneMeterRateLimitError) as err:
                # Don't retry auth or rate limit errors
                _LOGGER.error("%s", err)
                return {}
            except (aiohttp.ClientError, ValueError) as err:
                _LOGGER.warning(
                    "API error (attempt %s/%s): %s",
                    attempt + 1,
                    API_RETRY_ATTEMPTS,
                    err,
                )

            # Don't sleep on the last attempt
            if attempt < API_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(API_RETRY_DELAY)

        _LOGGER.error(
            "Failed to call OneMeter API after %s attempts: %s",
            API_RETRY_ATTEMPTS,
            url,
        )
        return {}

    async def get_all_devices(self) -> dict[str, Any]:
        """Get a list of all devices from the API."""
        return await self.api_call("devices")

    async def get_device_data(self) -> dict[str, Any]:
        """Get device data from the API."""
        return await self.api_call(f"devices/{self.device_id}")

    async def get_readings(
        self, count: int = 1, obis_codes: list[str] | None = None
    ) -> dict[str, Any]:
        """Get readings data for specific OBIS codes."""
        if obis_codes is None:
            obis_codes = [
                OBIS_ENERGY_PLUS,
                OBIS_ENERGY_MINUS,
                OBIS_ENERGY_R1,
                OBIS_ENERGY_R4,
                OBIS_ENERGY_ABS,
                OBIS_POWER,
                OBIS_BATTERY_VOLTAGE,
                OBIS_METER_SERIAL,
                OBIS_TARIFF,
            ]

        params = {
            "obis": ",".join(obis_codes),
            "count": count,
        }

        return await self.api_call(f"devices/{self.device_id}/readings", params)

    def extract_device_value(self, data: dict[str, Any], obis_code: str) -> Any:
        """Extract a value from device data by OBIS code.

        Args:
            data: Device data from the API
            obis_code: OBIS code to extract

        Returns:
            The extracted value or None if not found
        """
        if not data or not isinstance(data, dict) or not obis_code:
            return None

        try:
            # Try to find the value in different possible data structures
            if RESP_DEVICES in data and isinstance(data[RESP_DEVICES], list) and data[RESP_DEVICES]:
                device = data[RESP_DEVICES][0]  # Assume first device
                if isinstance(device, dict) and RESP_LAST_READING in device:
                    last_reading = device[RESP_LAST_READING]
                    if isinstance(last_reading, dict) and RESP_OBIS in last_reading:
                        obis_data = last_reading[RESP_OBIS]
                        if isinstance(obis_data, dict) and obis_code in obis_data:
                            return obis_data[obis_code]

            # Alternative structure
            elif (RESP_LAST_READING in data and
                  isinstance(data[RESP_LAST_READING], dict) and
                  RESP_OBIS in data[RESP_LAST_READING]):
                obis_data = data[RESP_LAST_READING][RESP_OBIS]
                if isinstance(obis_data, dict) and obis_code in obis_data:
                    return obis_data[obis_code]
        except (KeyError, IndexError, TypeError) as err:
            _LOGGER.debug("Error extracting device value for %s: %s", obis_code, err)

        return None

    def extract_reading_value(self, data: dict[str, Any], obis_code: str) -> Any:
        """Extract a value from readings data by OBIS code.

        Args:
            data: Readings data from the API
            obis_code: OBIS code to extract

        Returns:
            The extracted value or None if not found
        """
        if not data or not isinstance(data, dict) or not obis_code:
            return None

        try:
            if "readings" in data and isinstance(data["readings"], list) and data["readings"]:
                reading = data["readings"][0]  # Get most recent reading
                if isinstance(reading, dict) and RESP_OBIS in reading:
                    obis_data = reading[RESP_OBIS]
                    if isinstance(obis_data, dict) and obis_code in obis_data:
                        return obis_data[obis_code]
                elif isinstance(reading, dict) and obis_code in reading:
                    # Direct key in reading
                    return reading[obis_code]
        except (KeyError, IndexError, TypeError) as err:
            _LOGGER.debug("Error extracting reading value for %s: %s", obis_code, err)

        return None

    def get_this_month_usage(self, data: dict[str, Any]) -> float | None:
        """Get this month's usage from device data.

        Args:
            data: Device data from the API

        Returns:
            This month's usage as a float, or None if not available
        """
        if not data or not isinstance(data, dict):
            return None

        try:
            # Try different possible data structures
            if (RESP_DEVICES in data and
                isinstance(data[RESP_DEVICES], list) and
                data[RESP_DEVICES]):

                device = data[RESP_DEVICES][0]
                if (isinstance(device, dict) and
                    RESP_USAGE in device and
                    isinstance(device[RESP_USAGE], dict) and
                    RESP_THIS_MONTH in device[RESP_USAGE]):

                    value = device[RESP_USAGE][RESP_THIS_MONTH]
                    if value is not None:
                        return float(value)

            elif (RESP_USAGE in data and
                  isinstance(data[RESP_USAGE], dict) and
                  RESP_THIS_MONTH in data[RESP_USAGE]):

                value = data[RESP_USAGE][RESP_THIS_MONTH]
                if value is not None:
                    return float(value)

        except (KeyError, IndexError, ValueError, TypeError) as err:
            _LOGGER.debug("Error extracting this month's usage: %s", err)

        return None

    def get_previous_month_usage(self, data: dict[str, Any]) -> float | None:
        """Get previous month's usage from device data.

        Args:
            data: Device data from the API

        Returns:
            Previous month's usage as a float, or None if not available
        """
        if not data or not isinstance(data, dict):
            return None

        try:
            # Try different possible data structures
            if (RESP_DEVICES in data and
                isinstance(data[RESP_DEVICES], list) and
                data[RESP_DEVICES]):

                device = data[RESP_DEVICES][0]
                if (isinstance(device, dict) and
                    RESP_USAGE in device and
                    isinstance(device[RESP_USAGE], dict) and
                    RESP_PREV_MONTH in device[RESP_USAGE]):

                    value = device[RESP_USAGE][RESP_PREV_MONTH]
                    if value is not None:
                        return float(value)

            elif (RESP_USAGE in data and
                  isinstance(data[RESP_USAGE], dict) and
                  RESP_PREV_MONTH in data[RESP_USAGE]):

                value = data[RESP_USAGE][RESP_PREV_MONTH]
                if value is not None:
                    return float(value)

        except (KeyError, IndexError, ValueError, TypeError) as err:
            _LOGGER.debug("Error extracting previous month's usage: %s", err)

        return None

    async def close(self) -> None:
        """Close open client session."""
        if self._session:
            await self._session.close()
            self._session = None

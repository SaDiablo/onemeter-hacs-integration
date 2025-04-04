"""API client for OneMeter Cloud API."""
import asyncio
import datetime
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
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


class OneMeterApiClient:
    """API client for OneMeter Cloud."""

    def __init__(self, device_id: str, api_key: str):
        """Initialize the client."""
        self.device_id = device_id
        self.api_key = api_key

    async def api_call(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """Make an API call."""
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"X-Device-API-Key": self.api_key}

        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(API_TIMEOUT):
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            _LOGGER.error(
                                "API call error: %s - %s", response.status, await response.text()
                            )
                            return {}
            except asyncio.TimeoutError:
                _LOGGER.error("API timeout for %s", url)
                return {}
            except (aiohttp.ClientError, ValueError) as err:
                _LOGGER.error("API error: %s", err)
                return {}

    async def get_device_data(self) -> Dict[str, Any]:
        """Get device data from the API."""
        return await self.api_call(f"devices/{self.device_id}")

    async def get_readings(self, count: int = 1, obis_codes: List[str] = None) -> Dict[str, Any]:
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

    def extract_device_value(self, data: Dict[str, Any], obis_code: str) -> Any:
        """Extract a value from device data by OBIS code."""
        try:
            if RESP_DEVICES in data:
                device = data[RESP_DEVICES][0]  # Assume first device
                if RESP_LAST_READING in device and RESP_OBIS in device[RESP_LAST_READING]:
                    obis_data = device[RESP_LAST_READING][RESP_OBIS]
                    if obis_code in obis_data:
                        return obis_data[obis_code]
            elif RESP_LAST_READING in data and RESP_OBIS in data[RESP_LAST_READING]:
                obis_data = data[RESP_LAST_READING][RESP_OBIS]
                if obis_code in obis_data:
                    return obis_data[obis_code]
            return None
        except (KeyError, IndexError, TypeError):
            return None

    def extract_reading_value(self, data: Dict[str, Any], obis_code: str) -> Any:
        """Extract a value from readings data by OBIS code."""
        try:
            if data and len(data) > 0:
                reading = data[0]  # Get most recent reading
                if RESP_OBIS in reading and obis_code in reading[RESP_OBIS]:
                    return reading[RESP_OBIS][obis_code]
            return None
        except (KeyError, IndexError, TypeError):
            return None

    def get_this_month_usage(self, data: Dict[str, Any]) -> Optional[float]:
        """Get this month's usage from device data."""
        try:
            if RESP_DEVICES in data:
                device = data[RESP_DEVICES][0]
                if RESP_USAGE in device and RESP_THIS_MONTH in device[RESP_USAGE]:
                    return float(device[RESP_USAGE][RESP_THIS_MONTH])
            elif RESP_USAGE in data and RESP_THIS_MONTH in data[RESP_USAGE]:
                return float(data[RESP_USAGE][RESP_THIS_MONTH])
            return None
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    def get_previous_month_usage(self, data: Dict[str, Any]) -> Optional[float]:
        """Get previous month's usage from device data."""
        try:
            if RESP_DEVICES in data:
                device = data[RESP_DEVICES][0]
                if RESP_USAGE in device and RESP_PREV_MONTH in device[RESP_USAGE]:
                    return float(device[RESP_USAGE][RESP_PREV_MONTH])
            elif RESP_USAGE in data and RESP_PREV_MONTH in data[RESP_USAGE]:
                return float(data[RESP_USAGE][RESP_PREV_MONTH])
            return None
        except (KeyError, IndexError, ValueError, TypeError):
            return None

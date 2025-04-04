"""API client for OneMeter Cloud."""
import logging
import asyncio
import aiohttp
import async_timeout
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://cloud.onemeter.com/api"

# OBIS code constants based on API documentation
OBIS_ENERGY = "15_8_0"  # Energy A+ (total)
OBIS_ENERGY_PHASE1 = "15_8_1"  # Energy A+ (phase 1)
OBIS_VOLTAGE = "S_1_1_2"  # Battery voltage
OBIS_TIMESTAMP = "S_1_1_4"  # Timestamp of last reading
OBIS_BATTERY_LEVEL = "S_1_1_6"  # Battery level


class OneMeterApiClient:
    """API Client for OneMeter Cloud."""

    def __init__(self, device_id: str, api_key: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the API client.
        
        Args:
            device_id: The UUID of the OneMeter device
            api_key: Optional API key for authentication
            session: Optional aiohttp session
        """
        self._device_id = device_id
        self._api_key = api_key
        self._session = session or aiohttp.ClientSession()
        self._cached_data = {}
        self._last_update = None

    async def get_device_data(self) -> Optional[Dict[str, Any]]:
        """Get device data from OneMeter Cloud API.
        
        Returns:
            Device data dictionary or None if request failed
        """
        # Cache data for 5 minutes to avoid excessive API calls
        now = datetime.now()
        if self._last_update and now - self._last_update < timedelta(minutes=5) and self._cached_data:
            return self._cached_data

        if not self._api_key:
            _LOGGER.error("API key is required for OneMeter API")
            return None

        headers = {"Authorization": self._api_key}

        try:
            async with async_timeout.timeout(30):
                response = await self._session.get(
                    f"{API_BASE_URL}/devices/{self._device_id}", 
                    headers=headers
                )
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache successful results
                    self._cached_data = data
                    self._last_update = now
                    return data
                elif response.status == 401:
                    _LOGGER.error("API authentication error: Invalid API key")
                    return None
                else:
                    _LOGGER.error(f"API error: {response.status}")
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error(f"Error getting device data: {error}")
            return None

    async def get_readings(self, limit: int = 1, codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get latest meter readings from OneMeter Cloud API.
        
        Args:
            limit: Number of readings to retrieve (default: 1)
            codes: List of OBIS codes to retrieve
            
        Returns:
            Readings data dictionary or None if request failed
        """
        if not self._api_key:
            _LOGGER.error("API key is required for OneMeter API")
            return None

        headers = {"Authorization": self._api_key}
        
        params = {
            "limit": limit,
            "skip": 0,
            "sort": "descending"
        }
        
        if codes:
            params["codes"] = ",".join(codes)

        try:
            async with async_timeout.timeout(30):
                response = await self._session.get(
                    f"{API_BASE_URL}/devices/{self._device_id}/readings", 
                    headers=headers,
                    params=params
                )
                
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 401:
                    _LOGGER.error("API authentication error: Invalid API key")
                    return None
                else:
                    _LOGGER.error(f"API error: {response.status}")
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error(f"Error getting readings: {error}")
            return None

    async def get_summary(self, from_date: datetime, to_date: datetime) -> Optional[Dict[str, Any]]:
        """Get energy usage summary from OneMeter Cloud API.
        
        Args:
            from_date: Start date for summary
            to_date: End date for summary
            
        Returns:
            Summary data dictionary or None if request failed
        """
        if not self._api_key:
            _LOGGER.error("API key is required for OneMeter API")
            return None

        headers = {"Authorization": self._api_key}
        
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }

        try:
            async with async_timeout.timeout(30):
                response = await self._session.get(
                    f"{API_BASE_URL}/devices/{self._device_id}/report/summary", 
                    headers=headers,
                    params=params
                )
                
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 401:
                    _LOGGER.error("API authentication error: Invalid API key")
                    return None
                else:
                    _LOGGER.error(f"API error: {response.status}")
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error(f"Error getting summary: {error}")
            return None

    def extract_reading_value(self, readings_data: Dict[str, Any], obis_code: str) -> Optional[float]:
        """Extract value from readings response for a specific OBIS code.
        
        Args:
            readings_data: Readings data from API
            obis_code: OBIS code to extract
            
        Returns:
            Value for the OBIS code or None if not found
        """
        if not readings_data or "readings" not in readings_data or not readings_data["readings"]:
            return None
            
        # Get the latest reading
        latest_reading = readings_data["readings"][0]
        return latest_reading.get(obis_code)

    def extract_device_value(self, device_data: Dict[str, Any], obis_code: str) -> Optional[float]:
        """Extract value from device response for a specific OBIS code.
        
        Args:
            device_data: Device data from API
            obis_code: OBIS code to extract
            
        Returns:
            Value for the OBIS code or None if not found
        """
        if not device_data or not isinstance(device_data, dict):
            return None
            
        # Handle the case where we get a devices array
        if "devices" in device_data and isinstance(device_data["devices"], list) and len(device_data["devices"]) > 0:
            device_data = device_data["devices"][0]
            
        if "lastReading" in device_data and "OBIS" in device_data["lastReading"]:
            return device_data["lastReading"]["OBIS"].get(obis_code)
            
        return None
        
    def get_this_month_usage(self, device_data: Dict[str, Any]) -> Optional[float]:
        """Extract this month's energy usage from device data.
        
        Args:
            device_data: Device data from API
            
        Returns:
            This month's energy usage or None if not found
        """
        if not device_data or not isinstance(device_data, dict):
            return None
            
        # Handle the case where we get a devices array
        if "devices" in device_data and isinstance(device_data["devices"], list) and len(device_data["devices"]) > 0:
            device_data = device_data["devices"][0]
            
        if "usage" in device_data and "thisMonth" in device_data["usage"]:
            return device_data["usage"]["thisMonth"]
            
        return None
        
    def get_previous_month_usage(self, device_data: Dict[str, Any]) -> Optional[float]:
        """Extract previous month's energy usage from device data.
        
        Args:
            device_data: Device data from API
            
        Returns:
            Previous month's energy usage or None if not found
        """
        if not device_data or not isinstance(device_data, dict):
            return None
            
        # Handle the case where we get a devices array
        if "devices" in device_data and isinstance(device_data["devices"], list) and len(device_data["devices"]) > 0:
            device_data = device_data["devices"][0]
            
        if "usage" in device_data and "previousMonth" in device_data["usage"] and device_data["usage"]["previousMonth"] is not None:
            return device_data["usage"]["previousMonth"]
            
        return None
            
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()

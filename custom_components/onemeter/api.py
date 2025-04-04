"""API client for OneMeter Cloud."""
import logging
import asyncio
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://api.onemeter.com/v1"


class OneMeterApiClient:
    """API Client for OneMeter Cloud."""

    def __init__(self, username, password, api_key=None, session=None):
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._api_key = api_key
        self._session = session or aiohttp.ClientSession()
        self._auth_token = None

    async def authenticate(self):
        """Authenticate with the OneMeter API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(
                    f"{API_BASE_URL}/auth/login", 
                    json={"username": self._username, "password": self._password}
                )
                if response.status == 200:
                    data = await response.json()
                    self._auth_token = data.get("token")
                    return True
                else:
                    _LOGGER.error(f"Authentication failed: {response.status}")
                    return False
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error(f"Error connecting to OneMeter API: {error}")
            return False

    async def get_meter_data(self):
        """Get meter data from the OneMeter API."""
        if not self._auth_token:
            if not await self.authenticate():
                return None

        headers = {"Authorization": f"Bearer {self._auth_token}"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key

        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    f"{API_BASE_URL}/meters/readings/latest", 
                    headers=headers
                )
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    # Token expired, try to authenticate again
                    if await self.authenticate():
                        # Retry with new token
                        return await self.get_meter_data()
                    return None
                else:
                    _LOGGER.error(f"API error: {response.status}")
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError) as error:
            _LOGGER.error(f"Error getting meter data: {error}")
            return None

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()

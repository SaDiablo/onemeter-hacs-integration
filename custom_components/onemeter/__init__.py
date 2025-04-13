"""The OneMeter Cloud integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import OneMeterApiClient
from .const import CONF_DEVICE_ID, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def _verify_api_connection(client: OneMeterApiClient) -> None:
    """Verify that API connection works."""
    device_data = await client.get_device_data()
    if not device_data:
        raise ConfigEntryNotReady("Could not connect to OneMeter API")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OneMeter from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store API client for this entry
    api_key = entry.data[CONF_API_KEY]
    device_id = entry.data[CONF_DEVICE_ID]

    client = OneMeterApiClient(device_id=device_id, api_key=api_key)

    try:
        # Verify the API connection works
        await _verify_api_connection(client)
    except Exception as err:
        await client.close()
        raise ConfigEntryNotReady(f"Error connecting to OneMeter API: {err}") from err

    hass.data[DOMAIN][entry.entry_id] = client

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close the API client
        client: OneMeterApiClient = hass.data[DOMAIN].pop(entry.entry_id)
        await client.close()

        # Remove entry from hass data if it's the last entry
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # When options change (like refresh_interval), reload the integration
    await hass.config_entries.async_reload(entry.entry_id)

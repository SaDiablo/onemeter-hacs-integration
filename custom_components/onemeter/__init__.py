"""The OneMeter Cloud integration."""
import logging
from typing import Dict, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import OneMeterApiClient
from .const import DOMAIN, PLATFORMS, CONF_DEVICE_ID, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OneMeter from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    device_id = entry.data[CONF_DEVICE_ID]
    api_key = entry.data[CONF_API_KEY]
    
    # Create API client
    client = OneMeterApiClient(device_id=device_id, api_key=api_key)
    
    # Store API client and config entry
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "entry": entry,
    }
    
    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Close API client session
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        await client.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
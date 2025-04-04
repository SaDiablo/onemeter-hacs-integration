"""Config flow for OneMeter Cloud integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, List

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import OneMeterApiClient
from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

STEP_API_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): str,
})


async def get_available_devices(api_key: str) -> List[Dict[str, Any]]:
    """Get list of available devices using the API key."""
    devices = []
    client = OneMeterApiClient(device_id="", api_key=api_key)
    
    try:
        # Call the devices endpoint to list all available devices
        response = await client.get_all_devices()
        if response and "devices" in response:
            devices = response["devices"]
    finally:
        await client.close()
    
    return devices


class OneMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OneMeter Cloud."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self.api_key = None
        self.available_devices = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - API key input."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            
            try:
                # Test API key by listing available devices
                devices = await get_available_devices(api_key)
                
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    # Filter out already configured devices
                    current_ids = {
                        entry.data.get(CONF_DEVICE_ID)
                        for entry in self._async_current_entries()
                    }
                    
                    available_devices = [
                        device for device in devices
                        if device["_id"] not in current_ids
                    ]
                    
                    if not available_devices:
                        return self.async_abort(reason="no_unconfigured_devices")
                    
                    # API key works and devices found, proceed to device selection
                    self.api_key = api_key
                    self.available_devices = available_devices
                    return await self.async_step_device()
                    
            except Exception as ex:
                _LOGGER.exception("Error validating API key: %s", ex)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_API_DATA_SCHEMA, 
            errors=errors,
            description_placeholders={
                "api_key_info": "You can find your API key in your OneMeter Cloud account settings."
            }
        )

    async def async_step_device(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle device selection step."""
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            name = user_input.get(CONF_NAME, "")
            
            # Check if device is already configured
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            
            # Find the selected device in our list
            selected_device = None
            for device in self.available_devices:
                if device["_id"] == device_id:
                    selected_device = device
                    break
                    
            if selected_device:
                # Use the device name if custom name not provided
                if not name and "info" in selected_device and selected_device["info"].get("name"):
                    name = selected_device["info"]["name"]
                else:
                    name = name or f"OneMeter {device_id[-8:]}"
                    
                # Create the config entry
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_API_KEY: self.api_key,
                        CONF_NAME: name,
                    },
                )
            else:
                errors["base"] = "device_not_found"
        
        # Create device selection schema
        device_schema = vol.Schema({
            vol.Required(CONF_DEVICE_ID): vol.In({
                device["_id"]: device.get("info", {}).get("name", device["_id"]) 
                for device in self.available_devices
            }),
            vol.Optional(CONF_NAME): str,
        })
        
        return self.async_show_form(
            step_id="device", 
            data_schema=device_schema, 
            errors=errors,
            description_placeholders={
                "device_count": str(len(self.available_devices))
            }
        )
        
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OneMeterOptionsFlow(config_entry)
        
        
class OneMeterOptionsFlow(config_entries.OptionsFlow):
    """Handle OneMeter options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                "scan_interval",
                default=self.config_entry.options.get("scan_interval", 300),
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))

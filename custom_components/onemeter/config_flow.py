"""Config flow for OneMeter Cloud integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import OneMeterApiClient
from .const import CONF_DEVICE_ID, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    device_id = data[CONF_DEVICE_ID]
    api_key = data[CONF_API_KEY]

    client = OneMeterApiClient(device_id=device_id, api_key=api_key)
    
    # Test connection to OneMeter API
    device_data = await client.get_device_data()

    if not device_data:
        raise ValueError("Unable to connect to OneMeter API with provided credentials")

    # Close the session
    await client.close()

    # Return device info
    return {"title": data.get(CONF_NAME, DEFAULT_NAME)}


class OneMeterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OneMeter Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"
                if isinstance(ex, ValueError):
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

"""Config flow for OneMeter Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME

from .api import OneMeterApiClient
from .const import (
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    REFRESH_INTERVAL_1,
    REFRESH_INTERVAL_5,
    REFRESH_INTERVAL_15,
)

_LOGGER = logging.getLogger(__name__)

STEP_API_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


async def get_available_devices(api_key: str) -> list[dict[str, Any]]:
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


class OneMeterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OneMeter Cloud."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.api_key: str | None = None
        self.available_devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - API key input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            try:
                # Test API key by listing available devices
                devices = await get_available_devices(api_key)

                if not devices:
                    errors["base"] = "no_devices"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=STEP_API_DATA_SCHEMA,
                        errors=errors,
                        description_placeholders={
                            "api_key_info": "You can find your API key in your OneMeter Cloud account settings."
                        },
                    )

                # Filter out already configured devices
                current_ids = {
                    entry.data.get(CONF_DEVICE_ID)
                    for entry in self._async_current_entries()
                }

                available_devices = [
                    device for device in devices if device["_id"] not in current_ids
                ]

                if not available_devices:
                    return self.async_abort(reason="no_unconfigured_devices")

                # API key works and devices found, proceed to device selection
                self.api_key = api_key
                self.available_devices = available_devices
                return await self.async_step_device()

            except Exception:
                _LOGGER.exception("Error validating API key")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_API_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_key_info": "You can find your API key in your OneMeter Cloud account settings."
            },
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            name = user_input.get(CONF_NAME, "")

            # Check if device is already configured
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            # Find the selected device in our list
            selected_device = next(
                (
                    device
                    for device in self.available_devices
                    if device["_id"] == device_id
                ),
                None,
            )

            if selected_device:
                # Use the device name if custom name not provided
                if (
                    not name
                    and "info" in selected_device
                    and selected_device["info"].get("name")
                ):
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
                    options={
                        CONF_REFRESH_INTERVAL: DEFAULT_REFRESH_INTERVAL,
                    },
                )

            errors["base"] = "device_not_found"

        # Create device selection schema
        device_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): vol.In(
                    {
                        device["_id"]: device.get("info", {}).get("name", device["_id"])
                        for device in self.available_devices
                    }
                ),
                vol.Optional(CONF_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="device",
            data_schema=device_schema,
            errors=errors,
            description_placeholders={"device_count": str(len(self.available_devices))},
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return OneMeterOptionsFlow(config_entry)


class OneMeterOptionsFlow(OptionsFlow):
    """Handle OneMeter options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Create refresh interval options
        refresh_options = {
            REFRESH_INTERVAL_1: "1 minute",
            REFRESH_INTERVAL_5: "5 minutes",
            REFRESH_INTERVAL_15: "15 minutes (default)",
        }

        options = {
            vol.Required(
                CONF_REFRESH_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL
                ),
            ): vol.In(refresh_options)
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))

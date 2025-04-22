"""Tests for the OneMeter config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.onemeter.config_flow import OneMeterConfigFlow
from custom_components.onemeter.const import (
    CONF_API_KEY,
    CONF_DEVICE_ID,
    CONF_NAME,
    DOMAIN,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
)


@pytest.mark.asyncio
async def test_config_flow_user_step(hass: HomeAssistant, mock_get_available_devices):
    """Test the user step of the config flow."""
    # Set up mock for get_available_devices
    mock_get_available_devices.return_value = [
        {"_id": "device123", "info": {"name": "Test Device"}},
    ]
    
    # Initialize config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Check that the user form is shown
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "flow_id" in result
    
    # Complete the user step with API key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "api_key_test"}
    )
    
    # Check that we moved to device selection step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "device"
    
    # Complete the device step
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], 
        user_input={CONF_DEVICE_ID: "device123", CONF_NAME: "Custom Device Name"}
    )
    
    # Check that config entry was created
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Custom Device Name"
    assert result["data"] == {
        CONF_API_KEY: "api_key_test",
        CONF_DEVICE_ID: "device123",
        CONF_NAME: "Custom Device Name",
    }
    assert result["options"] == {
        CONF_REFRESH_INTERVAL: DEFAULT_REFRESH_INTERVAL,
    }


@pytest.mark.asyncio
async def test_config_flow_no_devices(hass: HomeAssistant, mock_get_available_devices):
    """Test the config flow when no devices are available."""
    # Set up mock to return empty list
    mock_get_available_devices.return_value = []
    
    # Initialize config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Complete the user step with API key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "api_key_test"}
    )
    
    # Check that we show error
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "no_devices"


@pytest.mark.asyncio
async def test_config_flow_already_configured(hass: HomeAssistant, mock_get_available_devices):
    """Test that a device cannot be configured twice."""
    # Set up mock for get_available_devices
    mock_get_available_devices.return_value = [
        {"_id": "device123", "info": {"name": "Test Device"}},
    ]
    
    # Configure the first device
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test Device",
        data={CONF_DEVICE_ID: "device123", CONF_API_KEY: "test_api_key"},
        source=config_entries.SOURCE_USER,
        options={},
        entry_id="test_entry_id"
    )
    
    # Add the entry to hass
    hass.config_entries.async_entries = lambda domain: [entry] if domain == DOMAIN else []
    
    # Initialize config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Complete the user step with API key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "api_key_test"}
    )
    
    # Should show device selection but with abort
    with patch.object(OneMeterConfigFlow, 'async_set_unique_id') as mock_set_id:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], 
            user_input={CONF_DEVICE_ID: "device123", CONF_NAME: "Custom Device Name"}
        )
        
    # Config should abort since device is already configured
    assert mock_set_id.called
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_config_flow_api_error(hass: HomeAssistant, mock_get_available_devices):
    """Test the config flow when API errors occur."""
    # Set up mock to raise an error
    mock_get_available_devices.side_effect = Exception("API Error")
    
    # Initialize config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Complete the user step with API key
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "api_key_test"}
    )
    
    # Check that we show error
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "unknown"
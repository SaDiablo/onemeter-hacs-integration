"""Tests for the OneMeter integration initialization."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.onemeter import (
    async_setup_entry,
    async_unload_entry,
    _verify_api_connection,
)
from custom_components.onemeter.const import DOMAIN, PLATFORMS


@pytest.mark.asyncio
async def test_verify_api_connection_success():
    """Test successful API connection verification."""
    # Create mock client with successful response
    client = AsyncMock()
    client.get_device_data = AsyncMock(return_value={"data": "valid"})
    
    # This should not raise an exception
    await _verify_api_connection(client)
    
    # Verify API was called
    client.get_device_data.assert_called_once()


@pytest.mark.asyncio
async def test_verify_api_connection_failure():
    """Test API connection verification with failure."""
    # Create mock client with empty response
    client = AsyncMock()
    client.get_device_data = AsyncMock(return_value={})
    
    # Should raise ConfigEntryNotReady
    with pytest.raises(ConfigEntryNotReady):
        await _verify_api_connection(client)
    
    # Verify API was called
    client.get_device_data.assert_called_once()


@pytest.mark.asyncio
async def test_verify_api_connection_exception():
    """Test API connection verification with exception."""
    # Create mock client that raises exception
    client = AsyncMock()
    client.get_device_data = AsyncMock(side_effect=Exception("API error"))
    
    # Should raise ConfigEntryNotReady
    with pytest.raises(ConfigEntryNotReady):
        await _verify_api_connection(client)
    
    # Verify API was called
    client.get_device_data.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_success(hass: HomeAssistant, mock_config_entry):
    """Test successful setup of a config entry."""
    # Mock the API client
    with patch(
        "custom_components.onemeter.OneMeterApiClient"
    ) as mock_api_client_class, patch(
        "custom_components.onemeter._verify_api_connection"
    ) as mock_verify:
        # Set up mock client
        mock_client = AsyncMock()
        mock_api_client_class.return_value = mock_client
        
        # Call setup_entry
        assert await async_setup_entry(hass, mock_config_entry)
        
        # Verify API client was created
        mock_api_client_class.assert_called_once()
        
        # Verify connection was verified
        mock_verify.assert_called_once_with(mock_client)
        
        # Check that platforms were set up
        for platform in PLATFORMS:
            assert f"{DOMAIN}.{platform}" in hass.config.components


@pytest.mark.asyncio
async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry):
    """Test failing setup of a config entry."""
    # Mock the API client
    with patch(
        "custom_components.onemeter.OneMeterApiClient"
    ) as mock_api_client_class, patch(
        "custom_components.onemeter._verify_api_connection",
        side_effect=ConfigEntryNotReady("Connection failed")
    ):
        # Set up mock client
        mock_client = AsyncMock()
        mock_api_client_class.return_value = mock_client
        
        # Setup should raise ConfigEntryNotReady
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)
        
        # Verify client was closed on failure
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading a config entry."""
    # First set up the entry
    with patch("custom_components.onemeter.async_setup_entry", return_value=True):
        # Mock that platforms are loaded
        for platform in PLATFORMS:
            hass.config.components.add(f"{platform}.{DOMAIN}")
            
        # Add client to hass data
        mock_client = AsyncMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_client}
        
        # Unload the entry
        assert await async_unload_entry(hass, mock_config_entry)
        
        # Verify client was closed
        mock_client.close.assert_called_once()
        
        # Verify entry was removed from hass data
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]

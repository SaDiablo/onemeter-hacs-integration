"""Tests for the OneMeter integration."""
from unittest.mock import patch, MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.onemeter.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test setting up the OneMeter integration."""
    with patch(
        "custom_components.onemeter.api.OneMeterApiClient.get_meter_data",
        return_value={"energy": 123.45, "power": 1500.0},
    ):
        entry = MagicMock()
        entry.data = {"username": "test_user", "password": "test_password"}
        entry.entry_id = "test_entry_id"
        
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        
        assert entry.state == ConfigEntryState.LOADED
        
        # Test sensors are created
        assert len(hass.states.async_entity_ids("sensor")) > 0